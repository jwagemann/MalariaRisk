class GoogleMapsWidget(widgets.DOMWidget):
    _view_name = traitlets.Unicode('GoogleMapsView', sync=True)
    value = traitlets.Unicode(sync=True)
    description = traitlets.Unicode(sync=True)
    lat = traitlets.CFloat(0, help="Center latitude, -90 to 90", sync=True)
    lng = traitlets.CFloat(0, help="Center longitude, -180 to 180", sync=True)
    zoom = traitlets.CInt(0, help="Zoom level, 0 to ~25", sync=True)
    bounds = traitlets.List([], help="Visible bounds, [W, S, E, N]", sync=True)
    
    def __init__(self, lng=0.0, lat=0.0, zoom=2):
        self.lng = lng
        self.lat = lat
        self.zoom = zoom
        
    def addLayer(self, image, vis_params, name=None, visible=True):
        mapid = image.getMapId(vis_params)
        self.send({'command':'addLayer', 'mapid': mapid['mapid'], 'token': mapid['token'], 'name': name, 'visible': visible})
        
    def center(self, lng, lat, zoom=None):
        self.send({'command': 'center', 'lng': lng, 'lat': lat, 'zoom': zoom})