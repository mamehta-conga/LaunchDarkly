import os
import ldclient
from ldclient import Context
from ldclient.config import Config
from threading import Lock, Event
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Set the SDK key based on environment
environment = os.getenv("ENVIRONMENT", "dev")
sdk_keys = {
    "dev": os.getenv("LAUNCHDARKLY_SDK_KEY_DEV"),
    "staging": os.getenv("LAUNCHDARKLY_SDK_KEY_STAGING"),
    "prod": os.getenv("LAUNCHDARKLY_SDK_KEY_PROD")
}

sdk_key = sdk_keys.get(environment)
if not sdk_key:
    print(f"*** SDK key for '{environment}' environment is not set.")
    exit(1)

# Set the feature flag key
feature_flag_key = os.getenv("LAUNCHDARKLY_FLAG_KEY", "sample-feature")

# Helper function to display feature flag evaluation result
def show_evaluation_result(key: str, value: bool):
    print(f"\n*** The {key} feature flag evaluates to {value}")

# Helper function to display LaunchDarkly banner
def show_banner():
    banner = """
        ██       
          ██     
      ████████   
         ███████ 
██ LAUNCHDARKLY █
         ███████ 
      ████████   
          ██     
        ██       
    """
    print(banner)

# Listener class for flag value changes
class FlagValueChangeListener:
    def __init__(self):
        self.__show_banner = True
        self.__lock = Lock()

    def flag_value_change_listener(self, flag_change):
        with self.__lock:
            if self.__show_banner and flag_change.new_value:
                show_banner()
                self.__show_banner = False

            show_evaluation_result(flag_change.key, flag_change.new_value)

def main():
    # Initialize LaunchDarkly SDK with provided key
    ldclient.set_config(Config(sdk_key))

    if not ldclient.get().is_initialized():
        print("*** SDK failed to initialize. Check internet connection and SDK key.")
        exit(1)

    print("*** SDK successfully initialized")

    # Set up the context for evaluating feature flags
    context = Context.builder('example-user-key').kind('user').name('Sandy').build()

    # Evaluate the feature flag
    flag_value = ldclient.get().variation(feature_flag_key, context, False)
    show_evaluation_result(feature_flag_key, flag_value)

    # Set up listener for flag value changes
    change_listener = FlagValueChangeListener()
    ldclient.get().flag_tracker.add_flag_value_change_listener(
        feature_flag_key, context, change_listener.flag_value_change_listener
    )

    # Keep the application running to listen for changes
    try:
        Event().wait()  # Keeps the thread alive indefinitely until interrupted
    except KeyboardInterrupt:
        print("\n*** Program interrupted. Exiting...")

    # Close the LaunchDarkly client when done
    ldclient.get().close()

if __name__ == "__main__":
    main()
