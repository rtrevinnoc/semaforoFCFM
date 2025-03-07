require "test_helper"

class SemaforosControllerTest < ActionDispatch::IntegrationTest
  setup do
    @semaforo = semaforos(:one)
  end

  test "should get index" do
    get semaforos_url
    assert_response :success
  end

  test "should get new" do
    get new_semaforo_url
    assert_response :success
  end

  test "should create semaforo" do
    assert_difference("Semaforo.count") do
      post semaforos_url, params: { semaforo: { id: @semaforo.id, name: @semaforo.name } }
    end

    assert_redirected_to semaforo_url(Semaforo.last)
  end

  test "should show semaforo" do
    get semaforo_url(@semaforo)
    assert_response :success
  end

  test "should get edit" do
    get edit_semaforo_url(@semaforo)
    assert_response :success
  end

  test "should update semaforo" do
    patch semaforo_url(@semaforo), params: { semaforo: { id: @semaforo.id, name: @semaforo.name } }
    assert_redirected_to semaforo_url(@semaforo)
  end

  test "should destroy semaforo" do
    assert_difference("Semaforo.count", -1) do
      delete semaforo_url(@semaforo)
    end

    assert_redirected_to semaforos_url
  end
end
