# mpris_feature.py

import urllib.parse
from thumbnail_gen import get_local_thumbnail
from get_youtube_thumbnail import get_youtube_thumbnail

try:
    import dbus
    import dbus.service
    import dbus.mainloop.glib
    from gi.repository import GLib
except ImportError:
    pass

class HardPlayerMPRIS(dbus.service.Object):
    def __init__(self, main_win):
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        bus_name = dbus.service.BusName('org.mpris.MediaPlayer2.hardplayer', bus=dbus.SessionBus())
        super(HardPlayerMPRIS, self).__init__(bus_name, '/org/mpris/MediaPlayer2')
        
        self.main_win = main_win
        self.player = main_win.player
        self._loop_status = "None" # الحالة الافتراضية للتكرار

        self.player.observe_property('pause', self.on_pause_change)
        self.player.observe_property('media-title', self.on_metadata_change)
        self.player.observe_property('duration', self.on_metadata_change)

    @dbus.service.signal('org.freedesktop.DBus.Properties', signature='sa{sv}as')
    def PropertiesChanged(self, interface, changed_properties, invalidated_properties):
        pass

    @dbus.service.signal('org.mpris.MediaPlayer2.Player', signature='x')
    def Seeked(self, position):
        pass

    def on_pause_change(self, name, value):
        status = 'Paused' if value else 'Playing'
        GLib.idle_add(self.PropertiesChanged, 'org.mpris.MediaPlayer2.Player', {'PlaybackStatus': status}, [])

    def on_metadata_change(self, name, value):
        metadata = self.Get('org.mpris.MediaPlayer2.Player', 'Metadata')
        GLib.idle_add(self.PropertiesChanged, 'org.mpris.MediaPlayer2.Player', {'Metadata': metadata}, [])

    # === دالة لتحديث حالة التكرار عند تغييرها من البرنامج ===
    def update_loop_status(self, status: str):
        """يتم استدعاؤها من البرنامج (main.py) لتحديث حالة MPRIS عند النقر على الزر"""
        if status in ["None", "Track", "Playlist"] and self._loop_status != status:
            self._loop_status = status
            GLib.idle_add(self.PropertiesChanged, 'org.mpris.MediaPlayer2.Player', {'LoopStatus': dbus.String(status)}, [])

    @dbus.service.method('org.mpris.MediaPlayer2.Player', in_signature='', out_signature='')
    def PlayPause(self): 
        self.player.pause = not self.player.pause
    
    @dbus.service.method('org.mpris.MediaPlayer2.Player', in_signature='', out_signature='')
    def Play(self): 
        self.player.pause = False
    
    @dbus.service.method('org.mpris.MediaPlayer2.Player', in_signature='', out_signature='')
    def Pause(self): 
        self.player.pause = True
    
    @dbus.service.method('org.mpris.MediaPlayer2.Player', in_signature='', out_signature='')
    def Stop(self): 
        self.player.stop()

    @dbus.service.method('org.mpris.MediaPlayer2.Player', in_signature='', out_signature='')
    def Next(self): 
        GLib.idle_add(self.main_win.play_next)

    @dbus.service.method('org.mpris.MediaPlayer2.Player', in_signature='', out_signature='')
    def Previous(self): 
        GLib.idle_add(self.main_win.play_previous)

    @dbus.service.method('org.mpris.MediaPlayer2.Player', in_signature='x', out_signature='')
    def Seek(self, offset):
        current = getattr(self.player, 'time_pos', 0)
        if current is not None:
            new_pos = current + (offset / 1000000.0)
            self.player.time_pos = max(0, new_pos)
            GLib.idle_add(self.Seeked, int(self.player.time_pos * 1000000))

    @dbus.service.method('org.mpris.MediaPlayer2.Player', in_signature='ox', out_signature='')
    def SetPosition(self, track_id, position):
        self.player.time_pos = position / 1000000.0
        GLib.idle_add(self.Seeked, position)

    # === إضافة دعم للكتابة (Set) على خصائص DBus (للسماح لـ KDE Connect بالتغيير) ===
    @dbus.service.method('org.freedesktop.DBus.Properties', in_signature='ssv', out_signature='')
    def Set(self, interface, prop, value):
        if interface == 'org.mpris.MediaPlayer2.Player':
            if prop == 'LoopStatus':
                new_status = str(value)
                if new_status in ["None", "Track", "Playlist"]:
                    self._loop_status = new_status
                    # بث التغيير لباقي أجهزة DBus
                    self.PropertiesChanged('org.mpris.MediaPlayer2.Player', {'LoopStatus': dbus.String(new_status)}, [])
                    
                    # إبلاغ النافذة الرئيسية لتحديث MPV والواجهة (UI)
                    if hasattr(self.main_win, 'handle_mpris_loop_change'):
                        GLib.idle_add(self.main_win.handle_mpris_loop_change, new_status)

    @dbus.service.method('org.freedesktop.DBus.Properties', in_signature='ss', out_signature='v')
    def Get(self, interface, prop):
        if interface == 'org.mpris.MediaPlayer2':
            if prop == 'Identity': return 'HardPlayer'
            if prop == 'CanQuit': return True
        
        if interface == 'org.mpris.MediaPlayer2.Player':
            if prop == 'PlaybackStatus': 
                return 'Paused' if self.player.pause else 'Playing'
            
            if prop == 'LoopStatus':
                return dbus.String(self._loop_status)
            
            if prop == 'Position': 
                pos = getattr(self.player, 'time_pos', 0)
                return dbus.Int64((pos or 0) * 1000000)

            if prop == 'Metadata':
                title = getattr(self.player, 'media_title', "HardPlayer") or "HardPlayer"
                path = getattr(self.player, 'path', "") or ""
                
                meta = {
                    'mpris:trackid': dbus.ObjectPath('/org/mpris/MediaPlayer2/TrackList/NoTrack'),
                    'xesam:title': dbus.String(title)
                }

                duration = getattr(self.player, 'duration', 0)
                if duration:
                    meta['mpris:length'] = dbus.Int64(duration * 1000000)

                # جلب الصورة المصغرة (يوتيوب أو محلي)
                if path.startswith('http'):
                    yt_thumb = get_youtube_thumbnail(path)
                    if yt_thumb:
                        meta['mpris:artUrl'] = dbus.String(yt_thumb)
                elif path:
                    meta['xesam:url'] = dbus.String(f"file://{urllib.parse.quote(path)}")
                    local_thumb = get_local_thumbnail(path)
                    if local_thumb:
                        meta['mpris:artUrl'] = dbus.String(f"file://{urllib.parse.quote(local_thumb)}")

                return dbus.Dictionary(meta, signature='sv')
            
            if prop == 'CanGoNext': return True
            if prop == 'CanGoPrevious': return True
            if prop == 'CanControl': return True
            if prop == 'CanPause': return True
            if prop == 'CanPlay': return True
            if prop == 'CanSeek': return True
            
        return ""

    @dbus.service.method('org.freedesktop.DBus.Properties', in_signature='s', out_signature='a{sv}')
    def GetAll(self, interface):
        if interface == 'org.mpris.MediaPlayer2.Player':
            return {
                'PlaybackStatus': self.Get(interface, 'PlaybackStatus'),
                'LoopStatus': self.Get(interface, 'LoopStatus'),
                'Metadata': self.Get(interface, 'Metadata'),
                'Position': self.Get(interface, 'Position'),
                'CanGoNext': True,
                'CanGoPrevious': True,
                'CanControl': True,
                'CanPause': True,
                'CanPlay': True,
                'CanSeek': True
            }
        return {}