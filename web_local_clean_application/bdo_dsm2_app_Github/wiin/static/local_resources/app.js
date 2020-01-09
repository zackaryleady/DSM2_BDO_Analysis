var map, featureList, channelJSON, overlap;
var channelNos = [];
console.log(window.location.pathname);
var runid = JSON.parse(document.getElementById("myInputs").dataset.runid);
console.log(runid);
var scenarioid
var variableid

var myRun_el = document.getElementById("myRun");
console.log(myRun_el);
var len = runid.length;
for (var i=0; i<len; i++) {
	var opt = String(runid[i]);
	console.log(opt);
	var el = document.createElement("option");
	el.textContent = opt;
	el.value = opt;
	myRun_el.appendChild(el);
};

$(document).ready(function(){
	if (window.location.pathname == '/summary_table/'){
		$("#myRun").on('change',function() {
			var myRun_e = document.getElementById("myRun");
			var strmyRun = myRun_e.options[myRun_e.selectedIndex].text;
			console.log(strmyRun);
			if (strmyRun != 'Select Model Run'){
				$.post("/summary_table/",{'myRun' : strmyRun})
					.done(function(returnobj){
						table = JSON.parse(returnobj);
						Plotly.newPlot("full_summary_table", table.data, table.layout);
					});
			}
			return false;
		});
	}
});

$(document).ready(function(){
	if (window.location.pathname == '/summary5_table/'){
		$("#myRun").on('change',function() {
			var myRun_e = document.getElementById("myRun");
			var strmyRun = myRun_e.options[myRun_e.selectedIndex].text;
			console.log(strmyRun);
			if (strmyRun != 'Select Model Run'){
				$.post("/summary5_table/",{'myRun' : strmyRun})
					.done(function(returnobj){
						table = JSON.parse(returnobj);
						Plotly.newPlot("five_summary_table", table.data, table.layout);
					});
			}
			return false;
		});
	}
});

$(document).ready(function(){
	if (window.location.pathname == '/summary14_table/'){
		$("#myRun").on('change',function() {
			var myRun_e = document.getElementById("myRun");
			var strmyRun = myRun_e.options[myRun_e.selectedIndex].text;
			console.log(strmyRun);
			if (strmyRun != 'Select Model Run'){
				$.post("/summary14_table/",{'myRun' : strmyRun})
					.done(function(returnobj){
						table = JSON.parse(returnobj);
						Plotly.newPlot("fourteen_summary_table", table.data, table.layout);
					});
			}
			return false;
		});
	}
});

$(document).ready(function(){
	if (window.location.pathname == '/mfcn_table/'){
		$("#myRun").on('change',function() {
			var myRun_e = document.getElementById("myRun");
			var strmyRun = myRun_e.options[myRun_e.selectedIndex].text;
			console.log(strmyRun);
			if (strmyRun != 'Select Model Run'){
				$.post("/mfcn_table/",{'myRun' : strmyRun})
					.done(function(returnobj){
						table1 = JSON.parse(returnobj[0]);
						table2 = JSON.parse(returnobj[1]);
						Plotly.newPlot("mfcn_table1", table1.data, table1.layout);
						Plotly.newPlot("mfcn_table2", table2.data, table2.layout);
					});
			}
			return false;
		});
	}
});

$(document).ready(function(){
	if (window.location.pathname == '/mvcn_table/'){
		$("#myRun").on('change',function() {
			var myRun_e = document.getElementById("myRun");
			var strmyRun = myRun_e.options[myRun_e.selectedIndex].text;
			console.log(strmyRun);
			if (strmyRun != 'Select Model Run'){
				$.post("/mvcn_table/",{'myRun' : strmyRun})
					.done(function(returnobj){
						table1 = JSON.parse(returnobj[0]);
						table2 = JSON.parse(returnobj[1]);
						Plotly.newPlot("mvcn_table1", table1.data, table1.layout);
						Plotly.newPlot("mvcn_table2", table2.data, table2.layout);
					});
			}
			return false;
		});
	}
});


$(document).ready(function(){
	if (window.location.pathname == '/'){
		var scenarioid = JSON.parse(document.getElementById("graphs").dataset.scenarioid);
		var variableid = JSON.parse(document.getElementById("graphs").dataset.variableid);
		console.log(scenarioid);
		console.log(variableid);
		var myVariable_el = document.getElementById("myVariable");
		console.log(myVariable_el);
		var myVariable_len = variableid.length;
		for (var i=0; i<myVariable_len; i++) {
			var opt = String(variableid[i]);
			var el = document.createElement("option");
			el.textContent = opt;
			el.value = opt;
			myVariable_el.appendChild(el);
		};
		
		
		//Add data to the GeoJSON and populate the dropdown menu
		$.getJSON("./static/local_resources/geom/channels.geojson", function (data) {
		  channelJSON.addData(data);
		  popDropdown(channelNos);
		  
		});
		//Create a GeoJSON container
		var channelJSON = L.geoJson(null, {
		  style: function (feature) {
			return {
			  color: getColor(feature.properties.channel_nu),
			  fill: false,
			  opacity: 1,
			  clickable: true,
			  weight: 4
			};
		  },
		  onEachFeature: function (feature, layer) {
		   //Bind popup
		   layer.bindPopup('Channel ' + feature.properties.channel_nu);   
		   
		   //Create a list of channel numbers to populate the dropdown
		   channelNos.push(parseInt(feature.properties.channel_nu,10));
		  
		   //Increase line width on mouseover
		   layer.on("mouseover", function (e) {
			   layer.setStyle({'weight': 7})
		   });
		   layer.on("mouseout", function (e) {
			   layer.setStyle({'weight': 4})
		   });
		   
		  }
		});
		// Initialize base layers
		var cartoLight = L.tileLayer("http://{s}.tiles.wmflabs.org/bw-mapnik/{z}/{x}/{y}.png", {
		  maxZoom: 19,
		  attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>' /* contributors, &copy; <a href="https://cartodb.com/attributions">CartoDB</a>' */
		});
		var usgsImagery = L.layerGroup([L.tileLayer("http://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer/tile/{z}/{y}/{x}", {
		  maxZoom: 15,
		}), L.tileLayer.wms("http://raster.nationalmap.gov/arcgis/services/Orthoimagery/USGS_EROS_Ortho_SCALE/ImageServer/WMSServer?", {
		  minZoom: 16,
		  maxZoom: 19,
		  layers: "0",
		  format: 'image/jpeg',
		  transparent: true,
		  attribution: "Aerial Imagery courtesy USGS"
		})]);


		// Initialize the map
		var map = L.map("map", {
		  zoom: 11,
		  center: [37.95,-121.56], 
		  layers: [cartoLight],
		  zoomControl: false,
		  attributionControl: false,
		});
		// Add the Channels to the map
		channelJSON.addTo(map);
		addLegend();
		// Add zoom button
		var zoomControl = L.control.zoom({
		  position: "bottomright"
		}).addTo(map);
		 
		// Add layer control (to switch basemaps and turn channels on and off) 
		var baseLayers = {
		  "Street Map": cartoLight,
		  "Aerial Imagery": usgsImagery,
		};
		var Overlays = {
			"Channels": channelJSON
		};
		L.control.layers(baseLayers,Overlays, {
			collapsed: isCollapsed
		}).addTo(map);

		// Leaflet patch to make layer control scrollable on touch browsers
		var container = $(".leaflet-control-layers")[0];
		if (!L.Browser.touch) {
		  L.DomEvent
		  .disableClickPropagation(container)
		  .disableScrollPropagation(container);
		} else {
		  L.DomEvent.disableClickPropagation(container);
		};
		
		function resetView() {
			map.setView([37.95,-121.56],11);
		}
		$("#zoomButton").click(function(){resetView()});
		
		$("#myRun").on('change',function() {
			var myRun_e = document.getElementById("myRun");			
			var myScenario_e = document.getElementById("myScenario");
			myScenario_e.innerHTML ="";
			var strmyRun = myRun_e.options[myRun_e.selectedIndex].text;
			var myScenario_len = scenarioid.length;
			for (var i=0; i<myScenario_len; i++) {
				//console.log(scenarioid[i]);
				//console.log(scenarioid[i].run_id);
				if (scenarioid[i].run_id == strmyRun){
					var el = document.createElement("option");
					var opt = scenarioid[i].scenario;
					el.textContent = opt;
					el.value = opt;
					myScenario_e.appendChild(el);
				}
				
			};

			
			var myVariable_e = document.getElementById("myVariable");
			
			var strmyScenario = myScenario_e.options[myScenario_e.selectedIndex].text;
			var strmyVariable = myVariable_e.options[myVariable_e.selectedIndex].text;
			var myChannel_e = document.getElementById('myDropdown');
			var strmyChannel = myChannel_e.options[myChannel_e.selectedIndex].text;
			console.log(strmyChannel);
			console.log(strmyRun);
			console.log(strmyScenario);
			console.log(strmyVariable);
			if (strmyRun != 'Select Model Run' & strmyScenario != 'Baseline vs. ?' & strmyVariable != 'Variable'){
				$.post("/",{'myRun' : strmyRun,'myScenario' : strmyScenario,'myVariable' : strmyVariable,'myChannel' : strmyChannel})
					.done(function(returnobj){
						//console.log(returnobj);
						graph = JSON.parse(returnobj[0]);
						overlap = JSON.parse(returnobj[1]);
						//console.log(overlap);
						if (graph != 'None'){
							Plotly.newPlot("myGraph", graph.data, graph.layout);
						}
						updateOverlap(overlap);
						updateLegend();
					});
			}
			return false;
		});
		$("#myScenario").on('change',function() {
			var myRun_e = document.getElementById("myRun");
			var myScenario_e = document.getElementById("myScenario");
			var myVariable_e = document.getElementById("myVariable");
			var strmyRun = myRun_e.options[myRun_e.selectedIndex].text;
			var strmyScenario = myScenario_e.options[myScenario_e.selectedIndex].text;
			var strmyVariable = myVariable_e.options[myVariable_e.selectedIndex].text;
			var myChannel_e = document.getElementById('myDropdown');
			var strmyChannel = myChannel_e.options[myChannel_e.selectedIndex].text;
			console.log(strmyChannel);
			console.log(strmyRun);
			console.log(strmyScenario);
			console.log(strmyVariable);
			if (strmyRun != 'Select Model Run' & strmyScenario != 'Baseline vs. ?' & strmyVariable != 'Variable'){
				$.post("/",{'myRun' : strmyRun,'myScenario' : strmyScenario,'myVariable' : strmyVariable,'myChannel' : strmyChannel})
					.done(function(returnobj){
						//console.log(returnobj);
						graph = JSON.parse(returnobj[0]);
						overlap = JSON.parse(returnobj[1]);
						//console.log(overlap);
						if (graph != 'None'){
							Plotly.newPlot("myGraph", graph.data, graph.layout);
						}
						updateOverlap(overlap);
						updateLegend();
					});
			}
			return false;
		});

		$("#myVariable").on('change',function() {
			var myRun_e = document.getElementById("myRun");
			var myScenario_e = document.getElementById("myScenario");
			var myVariable_e = document.getElementById("myVariable");
			var myChannel_e = document.getElementById('myDropdown');
			var strmyRun = myRun_e.options[myRun_e.selectedIndex].text;
			var strmyScenario = myScenario_e.options[myScenario_e.selectedIndex].text;
			var strmyVariable = myVariable_e.options[myVariable_e.selectedIndex].text;
			var strmyChannel = myChannel_e.options[myChannel_e.selectedIndex].text;
			console.log(strmyChannel);
			console.log(strmyRun);
			console.log(strmyScenario);
			console.log(strmyVariable);
			if (strmyRun != 'Select Model Run' & strmyScenario != 'Baseline vs. ?' & strmyVariable != 'Variable'){
				$.post("/",{'myRun' : strmyRun,'myScenario' : strmyScenario,'myVariable' : strmyVariable,'myChannel' : strmyChannel})
					.done(function(returnobj){
						//console.log(returnobj);
						graph = JSON.parse(returnobj[0]);
						overlap = JSON.parse(returnobj[1]);
						//console.log(overlap);
						if (graph != 'None'){
							Plotly.newPlot("myGraph", graph.data, graph.layout);
						}
						updateOverlap(overlap);
						updateLegend();
					});
			}
			return false;
		});
		$("#myDropdown").on('change',function(){
			var myRun_e = document.getElementById("myRun");
			var myScenario_e = document.getElementById("myScenario");
			var myVariable_e = document.getElementById("myVariable");
			var myChannel_e = document.getElementById('myDropdown');
			var strmyRun = myRun_e.options[myRun_e.selectedIndex].text;
			var strmyScenario = myScenario_e.options[myScenario_e.selectedIndex].text;
			var strmyVariable = myVariable_e.options[myVariable_e.selectedIndex].text;
			var strmyChannel = myChannel_e.options[myChannel_e.selectedIndex].text;
			//console.log(strmyChannel);
			//console.log(strmyRun);
			//console.log(strmyScenario);
			//console.log(strmyVariable);
			if (strmyRun != 'Select Model Run' & strmyScenario != 'Baseline vs. ?' & strmyVariable != 'Variable' & strmyChannel != 'Channel'){
				$.post(" ",{'myRun' : strmyRun,'myScenario' : strmyScenario,'myVariable' : strmyVariable,'myChannel' : strmyChannel})
					.done(function(returnobj){
						//console.log(returnobj);
						graph = JSON.parse(returnobj[0]);
						overlap = JSON.parse(returnobj[1]);
						//console.log(overlap);
						Plotly.newPlot("myGraph", graph.data, graph.layout);
						//updateOverlap(overlap);
						//updateLegend();			
						//console.log(String(graphurl));
						//var graph_dom = document.getElementById("myGraph");
						//graph_dom.data = String(graphurl);
					});
			}
			var a = parseInt(document.getElementById('myDropdown').value,10);
			if (Number.isInteger(a)) {
				channelJSON.eachLayer(function(layer) {
					if (layer.feature.properties.channel_nu == a) {
						map.fitBounds(layer.getBounds());
					}
				});
			}
			return false;

		});

		function updateLegend(){
			var leg = document.getElementById("legend-body");
			leg.innerHTML = "";
			//var grades = [300,250,220,200,150,100,80,50,20,10,0]; // Values displayed in the legend - MODIFY THIS!!!
			//var grades = [0.98,0.96,0.94,0.92,0.90,0.85,0.80,0.70,0.50,0.30,0];
			var grades = [0.80, 0.70, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.01, 0];
			for(var i=0; i <grades.length; i++){
				//Creates a rectangle with the color defined by grades[i] and displays text of "> "grades[i]
				leg.innerHTML+='<i class="rectangle" style="background:'+getOverlapColor(grades[i])+ '"></i> '+"> "+grades[i]+'<br/>';
			} 
		};

		function updateOverlap(overlap){
			channelJSON.eachLayer(function(layer){
				console.log(overlap)
				//console.log(layer)
				channel_number = layer.feature.properties.channel_nu;
				//console.log(String(channel_number));
				overlap_color = getOverlapColor(overlap[String(channel_number)])
				layer.setStyle({
					color: overlap_color,
					fill: false,
					opacity: 1,
					clickable: true,
					weight: 4
				});
				


			});
		};
		function sizeLayerControl(){
		  $(".leaflet-control-layers").css("max-height", $("#map").height() - 50);
		}

		// Defines color scale - MODIFY THIS!!!
		function getColor(d) {
			return d > 300 ? '#00FF00' :
				   d > 250  ? '#33ff00' :
				   d > 220  ? '#66ff00' :
				   d > 200  ? '#99ff00' :
				   d > 150   ?  '#ccff00':
				   d > 100   ?  '#FFFF00':
				   d > 80   ?  '#FFCC00':
				   d > 50   ? '#ff9900' :
				   d > 20   ? '#ff6600' :
				   d > 10   ? '#FF3300' :
							  '#FF0000';
		}
		function getOverlapColor(d) {
			return d > 0.80  ? '#FF0000' :
				   d > 0.70  ? '#FF3300':
				   d > 0.60  ? '#FF6600' :
				   d > 0.50   ?  '#FF9900':
				   d > 0.40   ? '#FFCC00' :
				   d > 0.30   ? '#FFFF00' :
				   d > 0.20   ?  '#CCFF00':
				   d > 0.10   ? '#99FF00' :
				   d > 0.01   ? '#66FF00' :
				   d >= 0	?  '#33FF00' :
				   				'#000000';
		}
		// Populate the dropdown with the list of channel numbers
		function popDropdown(channelNos) {
			//sort the channel numbers numerically
			function sortNo(a,b) {
				return a-b;
			}
			channelNos.sort(sortNo);
			var select = document.getElementById('myDropdown');
			var l = channelNos.length;
			for (var i=0; i<l; i++) {
				var opt = channelNos[i];
				var el = document.createElement("option");
				el.textContent = opt;
				el.value = opt;
				select.appendChild(el);
				
			} 	
		};
		// Add legend. The legend is intialized in the html file, and then content is added here.
		function addLegend() {
			var leg = document.getElementById("legend-body");
			var grades = [300,250,220,200,150,100,80,50,20,10,0]; // Values displayed in the legend - MODIFY THIS!!!
			//var grades = [0.98,0.95,0.90,0.85,0.80,0.70,0.60,0.50,0.40,0.30,0];
			for(var i=0; i <grades.length; i++){
				//Creates a rectangle with the color defined by grades[i] and displays text of "> "grades[i]
				leg.innerHTML+='<i class="rectangle" style="background:'+getColor(grades[i])+ '"></i> '+"> "+grades[i]+'<br/>';
			} 
		};

				
	}
});


 

/* Larger screens get expanded layer control and visible sidebar */
if (document.body.clientWidth <= 767) {
  var isCollapsed = true;
} else {
  var isCollapsed = false;
}



$("#about-btn").click(function() {
  $("#aboutModal").modal("show");
  $(".navbar-collapse.in").collapse("hide");
  return false;
});
// Shop dropdown menu when the user clicks on it	
function showDropdown() {
    document.getElementById("myDropdown").classList.toggle("show");
};

// Close the dropdown menu if the user clicks outside of it
window.onclick = function(event) {
	if (!event.target.matches('.dropbtn')) {
		var dropdowns = document.getElementsByClassName("dropdown-content");
		var i;
		for (i = 0; i < dropdowns.length; i++) {
		  var openDropdown = dropdowns[i];
		  if (openDropdown.classList.contains('show')){
			openDropdown.classList.remove('show');
		  }
		}	
	}
};


 
