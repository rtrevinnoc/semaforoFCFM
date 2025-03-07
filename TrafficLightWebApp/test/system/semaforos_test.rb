require "application_system_test_case"

class SemaforosTest < ApplicationSystemTestCase
  setup do
    @semaforo = semaforos(:one)
  end

  test "visiting the index" do
    visit semaforos_url
    assert_selector "h1", text: "Semaforos"
  end

  test "should create semaforo" do
    visit semaforos_url
    click_on "New semaforo"

    fill_in "Id", with: @semaforo.id
    fill_in "Name", with: @semaforo.name
    click_on "Create Semaforo"

    assert_text "Semaforo was successfully created"
    click_on "Back"
  end

  test "should update Semaforo" do
    visit semaforo_url(@semaforo)
    click_on "Edit this semaforo", match: :first

    fill_in "Id", with: @semaforo.id
    fill_in "Name", with: @semaforo.name
    click_on "Update Semaforo"

    assert_text "Semaforo was successfully updated"
    click_on "Back"
  end

  test "should destroy Semaforo" do
    visit semaforo_url(@semaforo)
    click_on "Destroy this semaforo", match: :first

    assert_text "Semaforo was successfully destroyed"
  end
end
