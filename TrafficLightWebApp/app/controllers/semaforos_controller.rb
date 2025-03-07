class SemaforosController < ApplicationController
  before_action :set_semaforo, only: %i[ show edit update destroy ]

  # GET /semaforos or /semaforos.json
  def index
    @semaforos = Semaforo.all
  end

  # GET /semaforos/1 or /semaforos/1.json
  def show
  end

  # GET /semaforos/new
  def new
    @semaforo = Semaforo.new
  end

  # GET /semaforos/1/edit
  def edit
  end

  # POST /semaforos or /semaforos.json
  def create
    @semaforo = Semaforo.new(semaforo_params)

    respond_to do |format|
      if @semaforo.save
        format.html { redirect_to @semaforo, notice: "Semaforo was successfully created." }
        format.json { render :show, status: :created, location: @semaforo }
      else
        format.html { render :new, status: :unprocessable_entity }
        format.json { render json: @semaforo.errors, status: :unprocessable_entity }
      end
    end
  end

  # PATCH/PUT /semaforos/1 or /semaforos/1.json
  def update
    respond_to do |format|
      logger.debug "Params received: #{params.to_unsafe_h}"
      if @semaforo.update(semaforo_params)
        format.html { redirect_to @semaforo, notice: "Semaforo was successfully updated." }
        format.json { render :show, status: :ok, location: @semaforo }
      else
        format.html { render :edit, status: :unprocessable_entity }
        format.json { render json: @semaforo.errors, status: :unprocessable_entity }
      end
    end
  end

  # DELETE /semaforos/1 or /semaforos/1.json
  def destroy
    @semaforo.destroy!

    respond_to do |format|
      format.html { redirect_to semaforos_path, status: :see_other, notice: "Semaforo was successfully destroyed." }
      format.json { head :no_content }
    end
  end

  private
    # Use callbacks to share common setup or constraints between actions.
    def set_semaforo
      @semaforo = Semaforo.find(params.expect(:id))
    end

    # Only allow a list of trusted parameters through.
    def semaforo_params
      params.require(:semaforo).permit(
        :serial, :mode, :state, :zone, :cruce_id, 
        :priority, :cycles, :last_green_update, :last_update, 
        location: [:latitude, :longitude]
      )
    end
end