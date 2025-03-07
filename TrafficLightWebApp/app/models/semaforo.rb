class Semaforo
  include Mongoid::Document
  include Mongoid::Timestamps

  field :serial, type: String
  field :mode, type: Integer
  field :state, type: Integer
  field :zone, type: String
  field :cruce_id, type: Integer
  field :priority, type: Integer
  field :cycles, type: Integer
  field :last_green_update, type: DateTime
  field :last_update, type: DateTime

  embeds_one :location

  MANUAL = 0
  AUTOMATIC = 1
  validates_inclusion_of :mode, in: [MANUAL, AUTOMATIC]
  def get_mode
    case mode
      when MANUAL then 'Manual'
      when AUTOMATIC then 'Automatic'
    end
  end

  GREEN = 0
  YELLOW = 1
  RED = 2
  validates_inclusion_of :state, in: [GREEN, YELLOW, RED]
  def get_color
    case state
      when GREEN then 'Green'
      when YELLOW then 'Yellow'
      when RED then 'Red'
    end
  end

  validate :state_can_only_be_changed_if_mode_is_manual, if: :state_changed?
  def state_can_only_be_changed_if_mode_is_manual
    if mode != MANUAL
      errors.add(:state, "can only be changed when mode is Manual (0)")
    end
  end
end

class Location
  include Mongoid::Document

  field :latitude, type: Float
  field :longitude, type: Float

  embedded_in :device
end