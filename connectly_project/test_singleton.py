from singletons.config_manager import ConfigManager

# 1. Create two variables
config1 = ConfigManager()
config2 = ConfigManager()

# 2. Check if they are the exact same object
assert config1 is config2
print("Test 1 Passed: Both variables are the same object.")

# 3. Change a setting in one variable
config1.set_setting("DEFAULT_PAGE_SIZE", 50)

# 4. Check if the OTHER variable sees the change
assert config2.get_setting("DEFAULT_PAGE_SIZE") == 50
print("Test 2 Passed: Settings are shared globally.")