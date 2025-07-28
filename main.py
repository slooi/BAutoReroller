from app.controller import Controller
from events_and_config.events_and_config import Config

def main():
    config = Config()
    controller = Controller(config)
    controller.start()

if __name__ == "__main__":
    main()