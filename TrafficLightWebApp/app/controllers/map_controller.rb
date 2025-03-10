class MapController < ApplicationController
    before_action :authenticate_user!

    def index
        @is_admin = current_user.has_role?(:admin)
    end
end
