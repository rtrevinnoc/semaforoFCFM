import { Controller } from "@hotwired/stimulus"
import L from "leaflet"

export default class extends Controller {
  map;
  static values = {
    isAdmin: Boolean,
    redTrafficLightIcon: String,
    yellowTrafficLightIcon: String,
    greenTrafficLightIcon: String
  };

  trafficLights = [];
  trafficLightMarkers = [];
  trafficLightMarkerGroup = L.markerClusterGroup({
    disableClusteringAtZoom: 15,
    zoomToBoundsOnClick: true
  });
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

    this.addTrafficLights()

    if (this.isAdminValue) {
      this.map.on('click', this.onMapClick.bind(this))
    }
  }

  onMapClick(event) {
    const { lat, lng } = event.latlng
    this.showNewSemaphoreForm(lat, lng)
  }

  showNewSemaphoreForm(lat, lng) {
    const closestSemaphore = this.trafficLights.reduce((closest, semaphore) => {
      const distance = this.map.distance([lat, lng], [semaphore.location.latitude, semaphore.location.longitude]);
      return distance < closest.distance ? { semaphore, distance } : closest;
    }, { semaphore: null, distance: Infinity }).semaphore;

    const cruce_id = closestSemaphore ? closestSemaphore.cruce_id : '';
    const zone = closestSemaphore ? closestSemaphore.zone : '';

    const formHtml = `
      <form id="new-semaphore-form" class="p-2 px-4 space-y-2">
        <h3 class="text-lg font-bold">Nuevo Semaforo</h3>
        <div class="space-y-2">
          <label class="block">
            Serial:
            <input type="text" name="serial" class="block w-full mt-1 p-2 border rounded" required>
          </label>
          <label class="block">
            Cruce:
            <input type="text" name="cruce_id" value="${cruce_id}" class="block w-full mt-1 p-2 border rounded" required>
          </label>
          <label class="block">
            Zona:
            <input type="text" name="zone" value="${zone}" class="block w-full mt-1 p-2 border rounded" required>
          </label>
          <label class="block">
            Número de Ciclos:
            <input type="number" name="cycles" class="block w-full mt-1 p-2 border rounded" required>
          </label>
          <label class="block">
            Nivel de Prioridad:
            <input type="number" name="priority" class="block w-full mt-1 p-2 border rounded" required>
          </label>
        </div>
        <input type="hidden" name="latitude" value="${lat}">
        <input type="hidden" name="longitude" value="${lng}">
        <button type="submit" class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">Registrar</button>
      </form>
    `

    const popup = L.popup()
      .setLatLng([lat, lng])
      .setContent(formHtml)
      .openOn(this.map)

    document.getElementById('new-semaphore-form').addEventListener('submit', this.createTrafficLight.bind(this))
  }

  createTrafficLight(event) {
    event.preventDefault()
    const formData = new FormData(event.target)
    const data = {
      serial: formData.get('serial'),
      priority: formData.get('priority'),
      zone: formData.get('zone'),
      cycles: formData.get('cycles'),
      cruce_id: formData.get('cruce_id'),
      location: {
        latitude: formData.get('latitude'),
        longitude: formData.get('longitude')
      },
      mode: this.modes.Manual,
      state: this.colors.Red
    }

    fetch('/semaforos.json', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
      },
      body: JSON.stringify({ semaforo: data })
    })
      .then(response => response.json())
      .then(newSemaphore => {
        this.trafficLights.push(newSemaphore)
        const index = this.trafficLights.length - 1
        const marker = L.marker([newSemaphore.location.latitude, newSemaphore.location.longitude], { icon: this.getTrafficLightMarkerIcon(newSemaphore) })
          .addTo(this.map)
          .bindPopup(this.generateMainPopupContent(index), { autoClose: false })

        this.trafficLightMarkers.push(marker)
        this.map.closePopup()
      })
      .catch(error => console.error(error))
  }

  changeTrafficLight(trafficLight, successCallback, errorCallback) {
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

  generateMainPopupContent(index) {
    let popupContent = `
      <div class="p-2 space-y-4">
        <p class="text-center text-lg mb-2"><span class="font-bold">Número de Serie: </span>${this.trafficLights[index].serial}</p>
        <div class="flex justify-center gap-2">
          <button data-action="click->map#changeTrafficLightColor" data-map-index-param="${index}" data-map-color-param="${this.colors.Red}"
          class="w-6 h-6 rounded-full bg-red-500 border-none"></button>
          <button data-action="click->map#changeTrafficLightColor" data-map-index-param="${index}" data-map-color-param="${this.colors.Yellow}"
          class="w-6 h-6 rounded-full bg-yellow-500 border-none"></button>
          <button data-action="click->map#changeTrafficLightColor" data-map-index-param="${index}" data-map-color-param="${this.colors.Green}"
          class="w-6 h-6 rounded-full bg-green-500 border-none"></button>
        </div>
        <button data-action="click->map#changeTrafficLightMode" data-map-index-param="${index}" data-map-mode-param="${this.modes.Automatic}" class="w-full bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">Cambiar a Automatico</button>
    `;

    if (this.isAdminValue) {
      popupContent += `
        <button data-action="click->map#destroyTrafficLight" data-map-index-param="${index}" class="w-full bg-red-500 hover:bg-red-700 text-white font-bold py-2 px-4 rounded">Eliminar</button>
        <button data-action="click->map#openEditTrafficLightPopup" data-map-index-param="${index}" class="w-full bg-yellow-500 hover:bg-yellow-700 text-white font-bold py-2 px-4 rounded">Editar</button>
      `;
    }

    return popupContent += "</div>";
  }

  addTrafficLights() {
    fetch('/semaforos.json')  // Fetch JSON data from Rails
    .then(response => response.json())
    .then(data => {
      this.trafficLights = data;
      this.trafficLights.forEach((trafficLight, index) => {
        this.trafficLightMarkers[index] = L.marker([trafficLight.location.latitude, trafficLight.location.longitude], { icon: this.getTrafficLightMarkerIcon(trafficLight) })

        this.trafficLightMarkers[index]
          .addTo(this.trafficLightMarkerGroup)
          .bindPopup(this.generateMainPopupContent(index), { autoClose: false });
      });

      if (this.trafficLightMarkers.length > 0) {
        this.trafficLightMarkerGroup.addTo(this.map);
        this.map.fitBounds(this.trafficLightMarkerGroup.getBounds());
      }
    })
    .catch(error => alert("Failed to create traffic light"));
  }

  destroyTrafficLight({ params: { index } }) {

    fetch(`/semaforos/${this.trafficLights[index].id}.json`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
      }
    })
      .then(response => {
        if (response.ok) {
          this.map.removeLayer(this.trafficLightMarkers[index]);
          this.trafficLights.splice(index, 1);
          this.trafficLightMarkers.splice(index, 1);
        } else {
          alert('Failed to delete traffic light');
        }
      })
      .catch(error => console.error(error));
  }

  openEditTrafficLightPopup(event) {
    event.preventDefault();
    event.stopPropagation();
    const index = event.target.dataset.mapIndexParam;
    const trafficLight = this.trafficLights[index];
    const formHtml = `
      <form id="edit-semaphore-form" class="p-2 px-4 space-y-2">
        <h3 class="text-lg font-bold">Editar Semaforo</h3>
        <div class="space-y-2">
          <label class="block">
            Serial:
            <input type="text" name="serial" value="${trafficLight.serial}" class="block w-full mt-1 p-2 border rounded" required>
          </label>
          <label class="block">
            Cruce:
            <input type="text" name="cruce_id" value="${trafficLight.cruce_id}" class="block w-full mt-1 p-2 border rounded" required>
          </label>
          <label class="block">
            Zona:
            <input type="text" name="zone" value="${trafficLight.zone}" class="block w-full mt-1 p-2 border rounded" required>
          </label>
          <label class="block">
            Número de Ciclos:
            <input type="number" name="cycles" value="${trafficLight.cycles}" class="block w-full mt-1 p-2 border rounded" required>
          </label>
          <label class="block">
            Nivel de Prioridad:
            <input type="number" name="priority" value="${trafficLight.priority}" class="block w-full mt-1 p-2 border rounded" required>
          </label>
        </div>
        <input type="hidden" name="latitude" value="${trafficLight.location.latitude}">
        <input type="hidden" name="longitude" value="${trafficLight.location.longitude}">
        <button type="submit" class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">Guardar</button>
        <button type="button" data-action="click->map#backToMainPopupContent" data-map-index-param="${index}" id="back-button" class="bg-gray-500 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded">Volver</button>
      </form>
    `

    this.trafficLightMarkers[index].getPopup().setContent(formHtml);

    document.getElementById('edit-semaphore-form').addEventListener('submit', (event) => this.editTrafficLight(event, index))
  }

  backToMainPopupContent(event) {
      event.stopPropagation();
      const index = event.target.dataset.mapIndexParam;
      this.trafficLightMarkers[index].getPopup().setContent(this.generateMainPopupContent(index));
  }

  editTrafficLight(event, index) {
    event.preventDefault()
    const formData = new FormData(event.target)
    const data = {
      id: this.trafficLights[index].id,
      serial: formData.get('serial'),
      priority: formData.get('priority'),
      zone: formData.get('zone'),
      cycles: formData.get('cycles'),
      cruce_id: formData.get('cruce_id'),
      location: {
        latitude: formData.get('latitude'),
        longitude: formData.get('longitude')
      },
      mode: this.modes.Manual,
      state: this.colors.Red
    }

    this.changeTrafficLight(data, () => {}, () => { alert('Failed to update traffic light') });
  }
}