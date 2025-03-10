import { Controller } from "@hotwired/stimulus"

// Connects to data-controller="tooltip"
export default class extends Controller {
  static targets = ["userTooltip"];
  isTooltipVisible = false;
  
  connect() {
    this.hideUserTooltip();
  }

  showUserTooltip() {
    this.isTooltipVisible = true;
    this.userTooltipTarget.classList.remove("hidden");
  }

  hideUserTooltip() {
    this.isTooltipVisible = false;
    this.userTooltipTarget.classList.add("hidden");
  }

  toggleUserTooltip() {
    if (this.isTooltipVisible) {
      this.hideUserTooltip();
    } else {
      this.showUserTooltip();
    }
  }
}
