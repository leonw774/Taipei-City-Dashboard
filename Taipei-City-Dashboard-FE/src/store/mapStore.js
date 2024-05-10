// Developed by Taipei Urban Intelligence Center 2023-2024

/* mapStore */
/*
The mapStore controls the map and includes methods to modify it.

!! PLEASE BE SURE TO REFERENCE THE MAPBOX DOCUMENTATION IF ANYTHING IS UNCLEAR !!
https://docs.mapbox.com/mapbox-gl-js/guides/
*/
import { createApp, defineComponent, nextTick, ref } from "vue";
import { defineStore } from "pinia";
import mapboxGl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import axios from "axios";
import { Threebox } from "threebox-plugin";
import { bbox, booleanContains, booleanWithin, featureCollection, flatten, isolines, lineSplit, point, polygon, voronoi } from "@turf/turf"

// Other Stores
import { useAuthStore } from "./authStore";
import { useDialogStore } from "./dialogStore";

// Vue Components
import MapPopup from "../components/map/MapPopup.vue";

// Utility Functions or Configs
import mapStyle from "../assets/configs/mapbox/mapStyle.js";
import {
	MapObjectConfig,
	TaipeiTown,
	TaipeiVillage,
	TaipeiBuilding,
	TpDistrict,
	TpVillage,
	maplayerCommonPaint,
	maplayerCommonLayout,
} from "../assets/configs/mapbox/mapConfig.js";
import { savedLocations } from "../assets/configs/mapbox/savedLocations.js";
import { calculateGradientSteps } from "../assets/configs/mapbox/arcGradient";
// import { voronoi } from "../assets/utilityFunctions/voronoi.js";
import { interpolation } from "../assets/utilityFunctions/interpolation.js";
// import { marchingSquare } from "../assets/utilityFunctions/marchingSquare.js";

let taipeiPolygon = polygon([[
	[121.51840, 25.17195],
	[121.52360, 25.18261],
	[121.56061, 25.21125],
	[121.58707, 25.19396],
	[121.58095, 25.16780],
	[121.59074, 25.16462],
	[121.60833, 25.13056],
	[121.60833, 25.12987],
	[121.59915, 25.11201],
	[121.63081, 25.09608],
	[121.62194, 25.04081],
	[121.66552, 25.03083],
	[121.66460, 25.02279],
	[121.60129, 25.01351],
	[121.60328, 24.97775],
	[121.62545, 24.96998],
	[121.59777, 24.96014],
	[121.55878, 24.96388],
	[121.55312, 24.97996],
	[121.53140, 24.98925],
	[121.52911, 25.00727],
	[121.51504, 25.02085],
	[121.49210, 25.00519],
	[121.47986, 25.04053],
	[121.50097, 25.04635],
	[121.50601, 25.06436],
	[121.50051, 25.08680],
	[121.48200, 25.09926],
	[121.45509, 25.10203],
	[121.45646, 25.12821],
	[121.50312, 25.17418],
	[121.51840, 25.17195]
]]);
let taipeiBBox = bbox(taipeiPolygon);

export const useMapStore = defineStore("map", {
	state: () => ({
		// Array of layer IDs that are in the map
		currentLayers: [],
		// Array of layer IDs that are in the map and currently visible
		currentVisibleLayers: [],
		// Stores all map configs for all layers (to be used to render popups)
		mapConfigs: {},
		// Stores the mapbox map instance
		map: null,
		// Stores popup information
		popup: null,
		// Stores saved locations
		savedLocations: savedLocations,
		// Store currently loading layers,
		loadingLayers: [],
	}),
	getters: {},
	actions: {
		/* Initialize Mapbox */
		// 1. Creates the mapbox instance and passes in initial configs
		initializeMapBox() {
			this.map = null;
			const MAPBOXTOKEN = import.meta.env.VITE_MAPBOXTOKEN;
			mapboxGl.accessToken = MAPBOXTOKEN;
			this.map = new mapboxGl.Map({
				...MapObjectConfig,
				style: mapStyle,
			});
			this.map.addControl(new mapboxGl.NavigationControl());
			this.map.doubleClickZoom.disable();
			this.map
				.on("load", () => {
					this.initializeBasicLayers();
				})
				.on("click", (event) => {
					if (this.popup) {
						this.popup = null;
					}
					this.addPopup(event);
				})
				.on("idle", () => {
					this.loadingLayers = this.loadingLayers.filter(
						(el) => el !== "rendering"
					);
				});
		},
		// 2. Adds three basic layers to the map (Taipei District, Taipei Village labels, and Taipei 3D Buildings)
		// Due to performance concerns, Taipei 3D Buildings won't be added in the mobile version
		initializeBasicLayers() {
			const authStore = useAuthStore();
			if (!this.map) return;
			// Taipei District Labels
			fetch(`/mapData/taipei_town.geojson`)
				.then((response) => response.json())
				.then((data) => {
					this.map
						.addSource("taipei_town", {
							type: "geojson",
							data: data,
						})
						.addLayer(TaipeiTown);
				});
			// Taipei Village Labels
			fetch(`/mapData/taipei_village.geojson`)
				.then((response) => response.json())
				.then((data) => {
					this.map
						.addSource("taipei_village", {
							type: "geojson",
							data: data,
						})
						.addLayer(TaipeiVillage);
				});
			// Taipei 3D Buildings
			if (!authStore.isMobileDevice) {
				this.map
					.addSource("taipei_building_3d_source", {
						type: "vector",
						url: import.meta.env.VITE_MAPBOXTILE,
					})
					.addLayer(TaipeiBuilding);
			}
			// Taipei Village Boundaries
			this.map
				.addSource(`tp_village`, {
					type: "vector",
					scheme: "tms",
					tolerance: 0,
					tiles: [
						`${location.origin}/geo_server/gwc/service/tms/1.0.0/taipei_vioc:tp_village@EPSG:900913@pbf/{z}/{x}/{y}.pbf`,
					],
				})
				.addLayer(TpVillage);
			// Taipei District Boundaries
			this.map
				.addSource(`tp_district`, {
					type: "vector",
					scheme: "tms",
					tolerance: 0,
					tiles: [
						`${location.origin}/geo_server/gwc/service/tms/1.0.0/taipei_vioc:tp_district@EPSG:900913@pbf/{z}/{x}/{y}.pbf`,
					],
				})
				.addLayer(TpDistrict);

			this.addSymbolSources();
		},
		// 3. Adds symbols that will be used by some map layers
		addSymbolSources() {
			const images = [
				"metro",
				"triangle_green",
				"triangle_white",
				"bike_green",
				"bike_orange",
				"bike_red",
			];
			images.forEach((element) => {
				this.map.loadImage(
					`/images/map/${element}.png`,
					(error, image) => {
						if (error) throw error;
						this.map.addImage(element, image);
					}
				);
			});
		},
		// 4. Toggle district boundaries
		toggleDistrictBoundaries(status) {
			if (status) {
				this.map.setLayoutProperty(
					"tp_district",
					"visibility",
					"visible"
				);
			} else {
				this.map.setLayoutProperty("tp_district", "visibility", "none");
			}
		},

		// 5. Toggle village boundaries
		toggleVillageBoundaries(status) {
			if (status) {
				this.map.setLayoutProperty(
					"tp_village",
					"visibility",
					"visible"
				);
			} else {
				this.map.setLayoutProperty("tp_village", "visibility", "none");
			}
		},

		/* Adding Map Layers */
		// 1. Passes in the map_config (an Array of Objects) of a component and adds all layers to the map layer list
		addToMapLayerList(map_config) {
			map_config.forEach((element) => {
				let mapLayerId = `${element.index}-${element.type}`;
				// 1-1. If the layer exists, simply turn on the visibility and add it to the visible layers list
				if (
					this.currentLayers.find((element) => element === mapLayerId)
				) {
					this.loadingLayers.push("rendering");
					this.turnOnMapLayerVisibility(mapLayerId);
					if (
						!this.currentVisibleLayers.find(
							(element) => element === mapLayerId
						)
					) {
						this.currentVisibleLayers.push(mapLayerId);
					}
					return;
				}
				let appendLayer = { ...element };
				appendLayer.layerId = mapLayerId;
				// 1-2. If the layer doesn't exist, call an API to get the layer data
				this.loadingLayers.push(appendLayer.layerId);
				if (element.source === "geojson") {
					this.fetchLocalGeoJson(appendLayer);
				} else if (element.source === "raster") {
					this.addRasterSource(appendLayer);
				}
			});
		},
		// 2. Call an API to get the layer data
		fetchLocalGeoJson(map_config) {
			axios
				.get(`/mapData/${map_config.index}.geojson`)
				.then((rs) => {
					this.addGeojsonSource(map_config, rs.data);
				})
				.catch((e) => console.error(e));
		},
		// 3-1. Add a local geojson as a source in mapbox
		addGeojsonSource(map_config, data) {
			if (map_config['value_replace'] !== undefined) {
				for (let i = 0; i < data.features.length; i++) {
					let properties = data.features[i].properties;
					for (let key in map_config.value_replace) {
						if (properties[key] === undefined) {
							continue;
						}
						properties[key] = properties[key].replace(
							new RegExp(map_config.value_replace[key].pattern),
							map_config.value_replace[key].replacement
						);
					}
				}
			}
			if (!["voronoi", "isoline"].includes(map_config.type)) {
				this.map.addSource(`${map_config.layerId}-source`, {
					type: "geojson",
					data: { ...data },
				});
			}
			if (map_config.type === "arc") {
				this.AddArcMapLayer(map_config, data);
			} else if (map_config.type === "voronoi") {
				this.AddVoronoiMapLayer(map_config, data);
			} else if (map_config.type === "isoline") {
				this.AddIsolineMapLayer(map_config, data);
			} else {
				this.addMapLayer(map_config);
			}
		},
		// 3-2. Add a raster map as a source in mapbox
		addRasterSource(map_config) {
			this.map.addSource(`${map_config.layerId}-source`, {
				type: "vector",
				scheme: "tms",
				tolerance: 0,
				tiles: [
					`${location.origin}/geo_server/gwc/service/tms/1.0.0/taipei_vioc:${map_config.index}@EPSG:900913@pbf/{z}/{x}/{y}.pbf`,
				],
			});
			this.addMapLayer(map_config);
		},
		// 4-1. Using the mapbox source and map config, create a new layer
		// The styles and configs can be edited in /assets/configs/mapbox/mapConfig.js
		addMapLayer(map_config) {
			let extra_paint_configs = {};
			let extra_layout_configs = {};
			if (map_config.icon) {
				extra_paint_configs = {
					...maplayerCommonPaint[
						`${map_config.type}-${map_config.icon}`
					],
				};
				extra_layout_configs = {
					...maplayerCommonLayout[
						`${map_config.type}-${map_config.icon}`
					],
				};
			}
			if (map_config.size) {
				extra_paint_configs = {
					...extra_paint_configs,
					...maplayerCommonPaint[
						`${map_config.type}-${map_config.size}`
					],
				};
				extra_layout_configs = {
					...extra_layout_configs,
					...maplayerCommonLayout[
						`${map_config.type}-${map_config.size}`
					],
				};
			}
			this.loadingLayers.push("rendering");
			this.map.addLayer({
				id: map_config.layerId,
				type: map_config.type,
				"source-layer":
					map_config.source === "raster" ? map_config.index : "",
				paint: {
					...maplayerCommonPaint[`${map_config.type}`],
					...extra_paint_configs,
					...map_config.paint,
				},
				layout: {
					...maplayerCommonLayout[`${map_config.type}`],
					...extra_layout_configs,
				},
				source: `${map_config.layerId}-source`,
			});
			this.currentLayers.push(map_config.layerId);
			this.mapConfigs[map_config.layerId] = map_config;
			this.currentVisibleLayers.push(map_config.layerId);
			this.loadingLayers = this.loadingLayers.filter(
				(el) => el !== map_config.layerId
			);
		},
		// 4-2. Add Map Layer for Arc Maps
		AddArcMapLayer(map_config, data) {
			const authStore = useAuthStore();
			const lines = [...JSON.parse(JSON.stringify(data.features))];
			const arcInterval = 20;

			this.loadingLayers.push("rendering");

			for (let i = 0; i < lines.length; i++) {
				let line = [];
				let lngDif =
					lines[i].geometry.coordinates[1][0] -
					lines[i].geometry.coordinates[0][0];
				let lngInterval = lngDif / arcInterval;
				let latDif =
					lines[i].geometry.coordinates[1][1] -
					lines[i].geometry.coordinates[0][1];
				let latInterval = latDif / arcInterval;

				let maxElevation =
					Math.pow(Math.abs(lngDif * latDif), 0.5) * 80000;

				for (let j = 0; j < arcInterval + 1; j++) {
					let waypointElevation =
						Math.sin((Math.PI * j) / arcInterval) * maxElevation;
					line.push([
						lines[i].geometry.coordinates[0][0] + lngInterval * j,
						lines[i].geometry.coordinates[0][1] + latInterval * j,
						waypointElevation,
					]);
				}

				lines[i].geometry.coordinates = [...line];
			}

			const tb = (window.tb = new Threebox(
				this.map,
				this.map.getCanvas().getContext("webgl"), //get the context from the map canvas
				{ defaultLights: true }
			));

			const delay = authStore.isMobileDevice ? 2000 : 500;

			setTimeout(() => {
				this.map.addLayer({
					id: map_config.layerId,
					type: "custom",
					renderingMode: "3d",
					onAdd: function () {
						const paintSettings = map_config.paint
							? map_config.paint
							: { "arc-color": ["#ffffff"] };
						const gradientSteps = calculateGradientSteps(
							paintSettings["arc-color"][0],
							paintSettings["arc-color"][1]
								? paintSettings["arc-color"][1]
								: paintSettings["arc-color"][0],
							arcInterval + 1
						);
						for (let line of lines) {
							let lineOptions = {
								geometry: line.geometry.coordinates,
								color: 0xffffff,
								width: paintSettings["arc-width"]
									? paintSettings["arc-width"]
									: 2,
								opacity:
									paintSettings["arc-opacity"] ||
									paintSettings["arc-opacity"] === 0
										? paintSettings["arc-opacity"]
										: 0.5,
							};

							let lineMesh = tb.line(lineOptions);
							lineMesh.geometry.setColors(gradientSteps);
							lineMesh.material.vertexColors = true;

							tb.add(lineMesh);
						}
					},
					render: function () {
						tb.update(); //update Threebox scene
					},
				});
				this.currentLayers.push(map_config.layerId);
				this.mapConfigs[map_config.layerId] = map_config;
				this.currentVisibleLayers.push(map_config.layerId);
				this.loadingLayers = this.loadingLayers.filter(
					(el) => el !== map_config.layerId
				);
			}, delay);
		},
		// 4-3. Add Map Layer for Voronoi Maps
		// Developed by 00:21, Taipei Codefest 2023
		AddVoronoiMapLayer(map_config, data) {
			this.loadingLayers.push("rendering");

			let voronoi_source = {
				type: data.type,
				crs: data.crs,
				features: [taipeiPolygon],
			};

			// Get features alone
			let { features } = data;

			// Get coordnates alone
			let coords = features.map(
				(location) => location.geometry.coordinates
			);

			// Remove duplicate coordinates (so that they wont't cause problems in the Voronoi algorithm...)
			let shouldBeRemoved = coords.map((coord1, ind) => {
				return (
					coords.findIndex((coord2) => {
						return (
							coord2[0] === coord1[0] && coord2[1] === coord1[1]
						);
					}) !== ind
				);
			});

			features = features.filter((_, ind) => !shouldBeRemoved[ind]);
			coords = coords.filter((_, ind) => !shouldBeRemoved[ind]);

			// make turf points
			let pointCollection = featureCollection(
				coords.map(
					(coord) => point(coord)
				)
			);

			// Calculate cell for each coordinate
			let cells = voronoi(pointCollection, {"bbox": taipeiBBox});

			// Push cell outlines to source data
			for (let i = 0; i < cells.features.length; i++) {
				let curLineString = {
					...features[i],
					geometry: {
						type: "LineString",
						coordinates: cells.features[i].geometry.coordinates[0]
					},
				}

				// check if current line is in taipeiPolygon
				if (booleanWithin(curLineString, taipeiPolygon)) {
					voronoi_source.features.push(curLineString);
				}
				else {
					// split current line with taipeiPolygon and check each again
					let splitLines = lineSplit(curLineString, taipeiPolygon);
					splitLines.features.forEach(
						line => {
							if (booleanContains(taipeiPolygon, line)) {
								voronoi_source.features.push(line);
							}
						}
					)
				}
			}

			// Add source and layer
			this.map.addSource(`${map_config.layerId}-source`, {
				type: "geojson",
				data: { ...voronoi_source },
			});

			let new_map_config = { ...map_config };
			new_map_config.type = "line";
			this.addMapLayer(new_map_config);
		},
		// 4-4. Add Map Layer for Isoline Maps
		// Developed by 00:21, Taipei Codefest 2023
		AddIsolineMapLayer(map_config, data) {
			this.loadingLayers.push("rendering");

			let isoline_source = {
				type: data.type,
				crs: data.crs,
				features: [taipeiPolygon],
			};

			// Step 1: Generate a 2D scalar field from known data points
			// - Turn the original data into the format that can be accepted by interpolation()
			let propertyName = map_config.paint?.["isoline-key"] || "value";
			let dataPoints = data.features.map((item) => {
				return {
					x: item.geometry.coordinates[0],
					y: item.geometry.coordinates[1],
					value: item.properties[propertyName],
				};
			});

			let lngStart = taipeiBBox[0];
			let latStart = taipeiBBox[1];
			let lngEnd = taipeiBBox[2];
			let latEnd = taipeiBBox[3];

			let targetPoints = [];
			let gridSize = 0.001;
			let rowN = 0;
			let colN = 0;

			// - Generate target point coordinates
			for (let i = latStart; i <= latEnd; i += gridSize, rowN += 1) {
				colN = 0;
				for (let j = lngStart; j <= lngEnd; j += gridSize, colN += 1) {
					targetPoints.push({ x: j, y: i });
				}
			}

			// - Get target points interpolation result
			let interpolationResult = interpolation(dataPoints, targetPoints);

			// Step 2: Calculate isolines from the 2D scalar field
			// - Turn the interpolation result into the point collection
			let interpolatedPoints = [];
			for (let n = 0; n < interpolationResult.length; n++) {
				interpolatedPoints.push(point(
					[lngStart + n % colN * gridSize, latStart + Math.floor(n / colN) * gridSize],
					{"value": interpolationResult[n]}
				));
			}
			let interpolatedPointCollection = featureCollection(interpolatedPoints);
			// [0 1 ... 17] ==> [40, 42, 44 ... 74]
			let breaks = [...Array((74 - 40) / 2 + 1).keys()].map(v => (v * 2 + 40));
			let isoline_data = isolines(interpolatedPointCollection, breaks, {zProperty: "value"});
			// flatten from MultiLineString to LineString
			isoline_data = flatten(isoline_data);

			isoline_data.features = isoline_data.features.filter(
				curIsoLine => {
					// check if current line is in taipeiPolygon
					if (booleanWithin(curIsoLine, taipeiPolygon)) {
						isoline_source.features.push(curIsoLine);
					}
					else {
						// split current line with taipeiPolygon and check each again
						let splitLines = lineSplit(curIsoLine, taipeiPolygon);
						splitLines.features.forEach(
							line => {
								if (booleanContains(taipeiPolygon, line)) {
									isoline_source.features.push(line);
								}
							}
						)
					}
				}
			)
			// Step 3: Add source and layer
			this.map.addSource(`${map_config.layerId}-source`, {
				type: "geojson",

				data: { ...isoline_source },
			});

			delete map_config.paint?.["isoline-key"];

			let new_map_config = { ...map_config, type: "line" };
			this.addMapLayer(new_map_config);
		},
		//  5. Turn on the visibility for a exisiting map layer
		turnOnMapLayerVisibility(mapLayerId) {
			this.map.setLayoutProperty(mapLayerId, "visibility", "visible");
		},
		// 6. Turn off the visibility of an exisiting map layer but don't remove it completely
		turnOffMapLayerVisibility(map_config) {
			map_config.forEach((element) => {
				let mapLayerId = `${element.index}-${element.type}`;
				this.loadingLayers = this.loadingLayers.filter(
					(el) => el !== mapLayerId
				);

				if (this.map.getLayer(mapLayerId)) {
					this.map.setFilter(mapLayerId, null);
					this.map.setLayoutProperty(
						mapLayerId,
						"visibility",
						"none"
					);
				}
				this.currentVisibleLayers = this.currentVisibleLayers.filter(
					(element) => element !== mapLayerId
				);
			});
			this.removePopup();
		},

		/* Popup Related Functions */
		// 1. Adds a popup when the user clicks on a item. The event will be passed in.
		addPopup(event) {
			// Gets the info that is contained in the coordinates that the user clicked on (only visible layers)
			const clickFeatureDatas = this.map.queryRenderedFeatures(
				event.point,
				{
					layers: this.currentVisibleLayers,
				}
			);
			// Return if there is no info in the click
			if (!clickFeatureDatas || clickFeatureDatas.length === 0) {
				return;
			}
			// Parse clickFeatureDatas to get the first 3 unique layer datas, skip over already included layers
			const mapConfigs = [];
			const parsedPopupContent = [];
			let previousParsedLayer = "";

			for (let i = 0; i < clickFeatureDatas.length; i++) {
				if (mapConfigs.length === 3) break;
				if (previousParsedLayer === clickFeatureDatas[i].layer.id)
					continue;
				previousParsedLayer = clickFeatureDatas[i].layer.id;
				mapConfigs.push(this.mapConfigs[clickFeatureDatas[i].layer.id]);
				parsedPopupContent.push(clickFeatureDatas[i]);
			}
			// Create a new mapbox popup
			this.popup = new mapboxGl.Popup()
				.setLngLat(event.lngLat)
				.setHTML('<div id="vue-popup-content"></div>')
				.addTo(this.map);
			// Mount a vue component (MapPopup) to the id "vue-popup-content" and pass in data
			const PopupComponent = defineComponent({
				extends: MapPopup,
				setup() {
					// Only show the data of the topmost layer
					return {
						popupContent: parsedPopupContent,
						mapConfigs: mapConfigs,
						activeTab: ref(0),
					};
				},
			});
			// This helps vue determine the most optimal time to mount the component
			nextTick(() => {
				const app = createApp(PopupComponent);
				app.mount("#vue-popup-content");
			});
		},
		// 2. Remove the current popup
		removePopup() {
			if (this.popup) {
				this.popup.remove();
			}
			this.popup = null;
		},

		/* Functions that change the viewing experience of the map */
		// 1. Add new saved location that users can quickly zoom to
		addNewSavedLocation(name) {
			const coordinates = this.map.getCenter();
			const zoom = this.map.getZoom();
			const pitch = this.map.getPitch();
			const bearing = this.map.getBearing();
			this.savedLocations.push([coordinates, zoom, pitch, bearing, name]);
		},
		// 2. Zoom to a location
		// [[lng, lat], zoom, pitch, bearing, savedLocationName]
		easeToLocation(location_array) {
			this.map.easeTo({
				center: location_array[0],
				zoom: location_array[1],
				duration: 4000,
				pitch: location_array[2],
				bearing: location_array[3],
			});
		},
		// 3. Fly to a location
		flyToLocation(location_array) {
			this.map.flyTo({
				center: location_array,
				duration: 1000,
			});
		},
		// 4. Remove a saved location
		removeSavedLocation(index) {
			this.savedLocations.splice(index, 1);
		},
		// 5. Force map to resize after sidebar collapses
		resizeMap() {
			if (this.map) {
				setTimeout(() => {
					this.map.resize();
				}, 200);
			}
		},

		/* Map Filtering */
		// 1. Add a filter based on a each map layer's properties (byParam)
		filterByParam(map_filter, map_configs, xParam, yParam) {
			// If there are layers loading, don't filter
			if (this.loadingLayers.length > 0) return;
			const dialogStore = useDialogStore();
			if (!this.map || dialogStore.dialogs.moreInfo) {
				return;
			}
			map_configs.map((map_config) => {
				let mapLayerId = `${map_config.index}-${map_config.type}`;
				if (map_config && map_config.type === "arc") {
					// Only turn off original layer visibility
					this.map.setLayoutProperty(
						mapLayerId,
						"visibility",
						"none"
					);
					// Remove any existing filtered layer
					if (this.map.getLayer(`${mapLayerId}-filtered`)) {
						this.map.removeLayer(`${mapLayerId}-filtered`);
					}
					// Filter data to render new filtered layer
					let toBeFiltered = {
						...this.map.getSource(`${mapLayerId}-source`)._data,
					};
					if (xParam) {
						toBeFiltered.features = toBeFiltered.features.filter(
							(el) =>
								el.properties[map_filter.byParam.xParam] ===
								xParam
						);
					}
					if (yParam) {
						toBeFiltered.features = toBeFiltered.features.filter(
							(el) =>
								el.properties[map_filter.byParam.yParam] ===
								yParam
						);
					}
					map_config.layerId = `${mapLayerId}-filtered`;
					// Add new filtered layer
					this.AddArcMapLayer(map_config, toBeFiltered);
					return;
				}
				// If x and y both exist, filter by both
				if (
					map_filter.byParam.xParam &&
					map_filter.byParam.yParam &&
					xParam &&
					yParam
				) {
					this.map.setFilter(mapLayerId, [
						"all",
						["==", ["get", map_filter.byParam.xParam], xParam],
						["==", ["get", map_filter.byParam.yParam], yParam],
					]);
				}
				// If only y exists, filter by y
				else if (map_filter.byParam.yParam && yParam) {
					this.map.setFilter(mapLayerId, [
						"==",
						["get", map_filter.byParam.yParam],
						yParam,
					]);
				}
				// default to filter by x
				else if (map_filter.byParam.xParam && xParam) {
					this.map.setFilter(mapLayerId, [
						"==",
						["get", map_filter.byParam.xParam],
						xParam,
					]);
				}
			});
		},
		// 2. filter by layer name (byLayer)
		filterByLayer(map_configs, xParam) {
			const dialogStore = useDialogStore();
			// If there are layers loading, don't filter
			if (this.loadingLayers.length > 0) return;
			if (!this.map || dialogStore.dialogs.moreInfo) {
				return;
			}
			map_configs.map((map_config) => {
				let mapLayerId = `${map_config.index}-${map_config.type}`;
				if (map_config.title !== xParam) {
					this.map.setLayoutProperty(
						mapLayerId,
						"visibility",
						"none"
					);
				} else {
					this.map.setLayoutProperty(
						mapLayerId,
						"visibility",
						"visible"
					);
				}
			});
		},
		// 3. Remove any property filters on a map layer
		clearByParamFilter(map_configs) {
			const dialogStore = useDialogStore();
			if (!this.map || dialogStore.dialogs.moreInfo) {
				return;
			}
			map_configs.map((map_config) => {
				let mapLayerId = `${map_config.index}-${map_config.type}`;
				if (map_config && map_config.type === "arc") {
					if (this.map.getLayer(`${mapLayerId}-filtered`)) {
						this.map.removeLayer(`${mapLayerId}-filtered`);
					}
					this.currentLayers = this.currentLayers.filter(
						(item) => item !== `${mapLayerId}-filtered`
					);
					this.currentVisibleLayers =
						this.currentVisibleLayers.filter(
							(item) => item !== `${mapLayerId}-filtered`
						);
					this.map.setLayoutProperty(
						mapLayerId,
						"visibility",
						"visible"
					);
					return;
				}
				this.map.setFilter(mapLayerId, null);
			});
		},
		// 4. Remove any layer filters on a map layer.
		clearByLayerFilter(map_configs) {
			const dialogStore = useDialogStore();
			if (!this.map || dialogStore.dialogs.moreInfo) {
				return;
			}
			map_configs.map((map_config) => {
				let mapLayerId = `${map_config.index}-${map_config.type}`;
				this.map.setLayoutProperty(mapLayerId, "visibility", "visible");
			});
		},

		/* Clearing the map */
		// 1. Called when the user is switching between maps
		clearOnlyLayers() {
			this.currentLayers.forEach((element) => {
				this.map.removeLayer(element);
				if (this.map.getSource(`${element}-source`)) {
					this.map.removeSource(`${element}-source`);
				}
			});
			this.currentLayers = [];
			this.mapConfigs = {};
			this.currentVisibleLayers = [];
			this.removePopup();
		},
		// 2. Called when user navigates away from the map
		clearEntireMap() {
			this.currentLayers = [];
			this.mapConfigs = {};
			this.map = null;
			this.currentVisibleLayers = [];
			this.removePopup();
		},
	},
});
