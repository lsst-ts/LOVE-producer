import SALPY_scheduler
from producer import create_remote_and_controller, get_remote_values, launch_emitter_once


def test_emitted_data_is_read_correctly():
    # Arrange
    remote, controller = create_remote_and_controller(SALPY_scheduler)
    from emitter_example_dict import dictionary as ref_values

    # Act
    launch_emitter_once(controller, 1)

    import time  # wait a little for the data to be written
    time.sleep(0.1)

    values = get_remote_values(remote)

    # Assert
    assert str(ref_values) == str(values)
