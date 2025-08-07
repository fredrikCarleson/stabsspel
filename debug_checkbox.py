import json
import os
from game_management import save_checkbox_state, get_checkbox_state

# Create test directory
test_dir = 'test_temp'
os.makedirs(test_dir, exist_ok=True)

# Create test data
test_data = {'id': 'test', 'checkbox_states': {}}
test_file = os.path.join(test_dir, 'game_test.json')

# Save initial data
with open(test_file, 'w') as f:
    json.dump(test_data, f)

print("Initial data:", test_data)

# Test save_checkbox_state
save_checkbox_state('test', 'test_checkbox', True)

# Read back the data
with open(test_file, 'r') as f:
    result = json.load(f)

print("After save:", result)
print("Checkbox state:", get_checkbox_state(result, 'test_checkbox')) 