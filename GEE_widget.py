%%javascript
require(["widgets/js/widget"], function(WidgetManager){
    var maps = [];
    
    // Define the GoogleMapsView
    var GoogleMapsView = IPython.DOMWidgetView.extend({
        
        render: function() {
            // Resize widget element to be 100% wide
            this.$el.css('width', '100%');

            // iframe source;  just enough to load Google Maps and let us poll whether initialization is complete
            var src='<html style="height:100%"><head>' +
                '<scr'+'ipt src="http://maps.googleapis.com/maps/api/js?sensor=false"></scr'+'ipt>' +
                '<scr'+'ipt>google.maps.event.addDomListener(window,"load",function(){ready=true});</scr'+'ipt>' +
                '</head>' +
                '<body style="height:100%; margin:0px; padding:0px"></body></html>';
            
            // Create the Google Maps container element.
            this.$iframe = $('<iframe />')
                .css('width', '100%')
                .css('height', '300px')
                .attr('srcdoc', src)
                .appendTo(this.$el);
                        
            var self = this; // hold onto this for initMapWhenReady

            // Wait until maps library has finished loading in iframe, then create map
            function initMapWhenReady() {
                // Iframe document and window
                var doc = self.$iframe[0].contentDocument;
               var win = self.$iframe[0].contentWindow;
                if (!win || !win.ready) {
                    // Maps library not yet loaded;  try again soon
                    setTimeout(initMapWhenReady, 20);
                    return;
                }

                // Maps library finished loading.  Build map now.
                var mapOptions = {
                    center: new win.google.maps.LatLng(self.model.get('lat'), self.model.get('lng')),
                    zoom: self.model.get('zoom')
                };
                var mapDiv = $('<div />')
                    .css('width', '100%')
                    .css('height', '100%')
                    .appendTo($(doc.body));
                self.map = new win.google.maps.Map(mapDiv[0], mapOptions);
                
                
                // Add an event listeners for user panning, zooming, and resizing map
                // TODO(rsargent): Bind self across all methods, and save some plumbing here
                win.google.maps.event.addListener(self.map, 'bounds_changed', function () {
                    self.handleBoundsChanged();
                });
                
                self.initializeLayersControl();
            }
           initMapWhenReady();
        },
        
        LayersControl: function(widget, controlDiv, map) {
            var win = widget.$iframe[0].contentWindow;
            var chicago = new win.google.maps.LatLng(41.850033, -87.6500523);

            // Set CSS styles for the DIV containing the control
            // Setting padding to 5 px will offset the control
            // from the edge of the map.
            controlDiv.style.padding = '5px';

            // Set CSS for the control border.
            var $controlUI = $('<div />')
                .css('backgroundColor', 'white')
                .css('borderStyle', 'solid')
                .css('borderWidth', '1px')
                .css('cursor', 'pointer')
                .css('textAlign', 'center')
                .appendTo($(controlDiv));
            
            // Set CSS for the control interior.
            var $controlContents = $('<div />')
                .css('fontFamily', 'Arial,sans-serif')
                .css('fontSize', '12px')
                .css('paddingLeft', '4px')
                .css('paddingRight', '4px')
                .css('paddingTop', '0px')
                .css('paddingBottom', '0px')
                .appendTo($controlUI);
            
            this.$controlTable = $('<table />')
                .append($('<tr><td colspan=2>Layers</td></tr>'))
                .appendTo($controlContents);
        },

        initializeLayersControl: function() {
            var doc = this.$iframe[0].contentDocument;
            var win = this.$iframe[0].contentWindow;

            // Create the DIV to hold the control and call the LayersControl() constructor
            // passing in this DIV.
    
            var layersControlDiv = document.createElement('div');
            this.layersControl = new this.LayersControl(this, layersControlDiv, this.map);

            layersControlDiv.index = 1;
            this.map.controls[win.google.maps.ControlPosition.TOP_RIGHT].push(layersControlDiv);
        },
        
        // Map geometry changed (pan, zoom, resize)
        handleBoundsChanged: function() {
            this.model.set('lng', this.map.getCenter().lng());
            this.model.set('lat', this.map.getCenter().lat());
            this.model.set('zoom', this.map.getZoom());
            var bounds = this.map.getBounds();
            var playgroundCompatible = [bounds.getSouthWest().lng(), bounds.getSouthWest().lat(),
                                        bounds.getNorthEast().lng(), bounds.getNorthEast().lat()];
            this.model.set('bounds', playgroundCompatible);
            this.touch();
        },
        
        // Receive custom messages from Python backend
        on_msg: function(msg) {
            var win = this.$iframe[0].contentWindow;
            if (msg.command == 'addLayer') {
                this.addLayer(msg.mapid, msg.token, msg.name, msg.visible);
            } else if (msg.command == 'center') {
                this.map.setCenter(new win.google.maps.LatLng(msg.lat, msg.lng));
                if (msg.zoom !== null) {
                    this.map.setZoom(msg.zoom);
                }
            }
        },
        
        // Add an Earth Engine layer
        addLayer: function(mapid, token, name, visible) {
            var win = this.$iframe[0].contentWindow;
            var eeMapOptions = {
                getTileUrl: function(tile, zoom) {
                    var url = ['https://earthengine.googleapis.com/map',
                               mapid, zoom, tile.x, tile.y].join("/");
                    url += '?token=' + token
                    return url;
                },
                tileSize: new win.google.maps.Size(256, 256),
                opacity: visible ? 1.0 : 0.0,
            };
            
            // Create the overlay map type
            var mapType = new win.google.maps.ImageMapType(eeMapOptions);
                
            // Overlay the Earth Engine generated layer
            this.map.overlayMapTypes.push(mapType);

            // Update layer visibility control
            var maxSlider = 100;
            
            function updateOpacity() {
                mapType.setOpacity($checkbox[0].checked ? $slider[0].value / 100.0 : 0);
            }
            
            var $checkbox = $('<input type="checkbox">')
                .prop('checked', visible)
                .change(updateOpacity);
            
            var $slider = $('<input type="range" />')
                .prop('min', 0)
                .prop('max', maxSlider)
                .prop('value', maxSlider)
                .css('width', '60px')
                .on('input', updateOpacity);

            // If user doesn't specify a layer name, create a default
            if (name === null) {
                name = 'Layer ' + this.map.overlayMapTypes.length;
            }
            
            var $row = $('<tr />');
            $('<td align="left" />').append($checkbox).append(name).appendTo($row);
            $('<td />').append($slider).appendTo($row);

            this.layersControl.$controlTable.append($row);
        }
    });
    
    // Register the GoogleMapsView with the widget manager.
    WidgetManager.register_widget_view('GoogleMapsView', GoogleMapsView);
});