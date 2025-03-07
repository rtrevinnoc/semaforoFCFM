import { Controller } from "@hotwired/stimulus"
import L from "leaflet"

export default class extends Controller {
  map;
  static values = {
    redTrafficLightIcon: String,
    yellowTrafficLightIcon: String,
    greenTrafficLightIcon: String
  };

  trafficLights = [];
  trafficLightMarkers = [];
  trafficLightMarkerGroup;
  trafficLightMarkerIcons = {
    Red: L.icon({
      iconUrl: this.redTrafficLightIconValue,
      iconSize: [32, 32],
      iconAnchor: [16, 32],
      popupAnchor: [0, -32]
    }),
    Yellow: L.icon({
      iconUrl: this.yellowTrafficLightIconValue,
      iconSize: [32, 32],
      iconAnchor: [16, 32],
      popupAnchor: [0, -32]
    }),
    Green: L.icon({
      iconUrl: this.greenTrafficLightIconValue,
      iconSize: [32, 32],
      iconAnchor: [16, 32],
      popupAnchor: [0, -32]
    }),
  }

  modes = {
    Manual: 0,
    Automatic: 1
  };

  colors = {
    Red: 0,
    Yellow: 1,
    Green: 2,
  };

  connect() {
    this.initializeMap()
  }

  initializeMap() {
    this.map = L.map(this.element, { closePopupOnClick: false }).setView([25.800123, -100.392382], 13)

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(this.map)

    this.addTrafficLights(this.map)
  }

  changeTrafficLight(trafficLight, successCallback, errorCallback) {
    console.log(JSON.stringify({ "semaforo": trafficLight }))
    fetch(`/semaforos/${trafficLight.id}.json`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
      },
      body: JSON.stringify({ "semaforo": trafficLight })
    })
      .then(response => response.json())
      .then(data => {
        if (successCallback) successCallback(data);
      })
      .catch(error => {
        if (errorCallback) errorCallback(error);
      });
  }

  changeTrafficLightMode({ params: { index, mode } }) {
    this.trafficLights[index].mode = mode;

    this.changeTrafficLight(this.trafficLights[index], (trafficLight) => {
      this.trafficLights[index] = trafficLight
    })
  }

  getTrafficLightMarkerIcon(trafficLight) {
    switch (trafficLight.state) {
      case this.colors.Red:
        return this.trafficLightMarkerIcons.Red;
      case this.colors.Yellow:
        return this.trafficLightMarkerIcons.Yellow;
      case this.colors.Green:
        return this.trafficLightMarkerIcons.Green;
    }
  }

  changeTrafficLightColor({ params: { index, color } }) {
    this.trafficLights[index].mode = this.modes.Manual;
    this.trafficLights[index].state = color;

    this.changeTrafficLight(this.trafficLights[index], (trafficLight) => {
      this.trafficLights[index] = trafficLight
      this.trafficLightMarkers[index].setIcon(this.getTrafficLightMarkerIcon(trafficLight))
    })
  }

  generatePopupContent(index) {
    return `
      <p><strong>Serial: </strong>${this.trafficLights[index].serial}</p>
      <button data-action="click->map#changeTrafficLightMode" data-map-index-param="${index}" data-map-mode-param="${this.modes.Automatic}">Cambiar a Automatico</button>
      <div style="display: flex; justify-content: center; gap: 10px;">
        <button data-action="click->map#changeTrafficLightColor" data-map-index-param="${index}" data-map-color-param="${this.colors.Red}"
                style="width: 25px; height: 25px; border-radius: 50%; background-color: red; border: none;"></button>
        <button data-action="click->map#changeTrafficLightColor" data-map-index-param="${index}" data-map-color-param="${this.colors.Yellow}"
                style="width: 25px; height: 25px; border-radius: 50%; background-color: yellow; border: none;"></button>
        <button data-action="click->map#changeTrafficLightColor" data-map-index-param="${index}" data-map-color-param="${this.colors.Green}"
                style="width: 25px; height: 25px; border-radius: 50%; background-color: green; border: none;"></button>
      </div>
      
    `;
  }

  addTrafficLights() {
    fetch('/semaforos.json')  // Fetch JSON data from Rails
    .then(response => response.json())
    .then(data => {
      this.trafficLights = data;
      this.trafficLights.forEach((trafficLight, index) => {
        this.trafficLightMarkers[index] = L.marker([trafficLight.location.latitude, trafficLight.location.longitude], { icon: this.getTrafficLightMarkerIcon(trafficLight) })

        this.trafficLightMarkers[index]
          .addTo(this.map)
          .bindPopup(this.generatePopupContent(index), { autoClose: false });
      });

      if (this.trafficLightMarkers.length > 0) {
        this.trafficLightMarkerGroup = L.featureGroup(this.trafficLightMarkers).addTo(this.map);
        this.map.fitBounds(this.trafficLightMarkerGroup.getBounds());
      }
    })
    .catch(error => console.error(error));
  }
}