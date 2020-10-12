

def set_intended_for(image, intended_for):
    intended_for_path = intended_for.get_path().replace(
        intended_for.get_session().get_path(), "").strip("/")
    image.add_metadata("IntendedFor", intended_for_path)

