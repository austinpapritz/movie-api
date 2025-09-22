# test_api_key_generation.py
import pytest
import secrets
import string
from collections import Counter

def generate_api_key(prefix="sk_movie_") -> str:
    """Your current generation method"""
    random_part = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
    return f"{prefix}{random_part}"

class TestAPIKeyGeneration:
    
    def test_key_format(self):
        """Test that keys have correct format"""
        key = generate_api_key()
        
        # Check prefix
        assert key.startswith("sk_movie_")
        
        # Check total length (9 chars prefix + 32 chars random = 41 total)
        assert len(key) == 41
        
        # Check that random part only contains valid characters
        random_part = key[9:]  # Skip "sk_movie_" prefix
        valid_chars = set(string.ascii_letters + string.digits)
        assert all(c in valid_chars for c in random_part)
    
    def test_uniqueness(self):
        """Test that generated keys are unique"""
        keys = [generate_api_key() for _ in range(1000)]
        
        # All keys should be unique
        assert len(keys) == len(set(keys))
    
    def test_randomness_distribution(self):
        """Test that character distribution is roughly uniform"""
        keys = [generate_api_key() for _ in range(100)]
        
        # Extract all random characters
        all_chars = ''.join(key[9:] for key in keys)  # Skip prefix
        char_counts = Counter(all_chars)
        
        # Should have a reasonable distribution
        # With 62 possible chars and ~3200 total chars, expect ~51-52 per char
        expected_count = len(all_chars) / 62
        
        for char, count in char_counts.items():
            # Allow 50% variance from expected (very loose test)
            assert count > expected_count * 0.5
            assert count < expected_count * 1.5
    
    def test_no_predictable_patterns(self):
        """Test that consecutive keys don't have predictable patterns"""
        key1 = generate_api_key()
        key2 = generate_api_key()
        
        # Keys should not be sequential or similar
        random_part1 = key1[9:]
        random_part2 = key2[9:]
        
        # Count different characters
        differences = sum(c1 != c2 for c1, c2 in zip(random_part1, random_part2))
        
        # Should differ in most positions (expect ~31 out of 32)
        assert differences > 25
    
    def test_performance(self):
        """Test generation performance"""
        import time
        
        start_time = time.time()
        keys = [generate_api_key() for _ in range(1000)]
        end_time = time.time()
        
        generation_time = end_time - start_time
        
        # Should generate 1000 keys in under 1 second
        assert generation_time < 1.0
        
        # Average should be very fast
        avg_time = generation_time / 1000
        assert avg_time < 0.001  # Less than 1ms per key
    
    def test_custom_prefix(self):
        """Test that custom prefixes work"""
        key = generate_api_key("test_")
        assert key.startswith("test_")
        assert len(key) == 37  # 5 chars prefix + 32 chars random

if __name__ == "__main__":
    # Run tests manually
    test = TestAPIKeyGeneration()
    
    print("🧪 Running API Key Generation Tests...")
    
    try:
        test.test_key_format()
        print("✅ Format test passed")
        
        test.test_uniqueness()
        print("✅ Uniqueness test passed")
        
        test.test_randomness_distribution()
        print("✅ Randomness test passed")
        
        test.test_no_predictable_patterns()
        print("✅ Pattern test passed")
        
        test.test_performance()
        print("✅ Performance test passed")
        
        test.test_custom_prefix()
        print("✅ Custom prefix test passed")
        
        print("\n🎉 All tests passed! Your API key generation is solid.")
        
    except AssertionError as e:
        print(f"❌ Test failed: {e}")
    except Exception as e:
        print(f"💥 Unexpected error: {e}")