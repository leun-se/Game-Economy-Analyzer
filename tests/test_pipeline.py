import sys
import os
# Add the parent directory (root folder) to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
from pipeline import validate_drop

# Test Case 1: Valid item
def test_valid_drop_is_accepted():
    # use ARRANGE, ACT, ASSERT framework
    good_record = {"item": "Steel Sword", "value": 50}
    
    is_valid, reason = validate_drop(good_record)
    
    assert is_valid == True
    assert reason == "Valid"

# Test Case 2: Negative value glitch
def test_negative_value_is_rejected():
    bad_record = {"item": "GlitchItem", "value": -100}
    
    is_valid, reason = validate_drop(bad_record)
    
    assert is_valid == False
    assert reason == "Negative Gold Value"

# Test Case 3: The Missing Name Bug
def test_empty_name_is_rejected():
    bad_record = {"item": "", "value": 10}

    is_valid, reason = validate_drop(bad_record)

    assert is_valid == False
    assert reason == "Missing Item Name"

# Test Case 4: The "Game Breaking" Value
def test_value_too_high_is_rejected():
    god_mode_record = {"item": "Hacked Sword", "value": 1000000}

    is_valid, reason = validate_drop(god_mode_record)

    assert is_valid == False
    assert reason == "Value Exceeds Limit"
