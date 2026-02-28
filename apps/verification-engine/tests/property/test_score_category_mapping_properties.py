"""
Property-based tests for score-to-category mapping.

Property 6: Score-to-Category Mapping
**Validates: Requirements 4.5, 4.6, 4.7, 4.8, 4.9**

Property: For any credibility score in the range [0, 100], the system should map it 
to exactly one category: "Verified False" (0-39), "Likely False" (40-59), "Uncertain" (60-69), 
"Likely True" (70-84), or "Verified True" (85-100).
"""
import pytest
from hypothesis import given, strategies as st, settings
from src.services.scorer import CredibilityScorer


class TestScoreCategoryMappingProperties:
    """Property-based tests for score-to-category mapping."""
    
    @given(st.integers(min_value=0, max_value=100))
    @settings(max_examples=100)
    def test_every_score_maps_to_exactly_one_category(self, score):
        """
        Property 6: Complete Coverage
        **Validates: Requirements 4.5, 4.6, 4.7, 4.8, 4.9**
        
        Every score in the range [0, 100] should map to exactly one valid category.
        """
        scorer = CredibilityScorer()
        category = scorer._map_score_to_category(score)
        
        # Property: Category must be one of the five valid categories
        valid_categories = [
            "Verified False",
            "Likely False",
            "Uncertain",
            "Likely True",
            "Verified True"
        ]
        
        assert category in valid_categories, (
            f"Score {score} mapped to invalid category '{category}'"
        )
    
    @given(st.integers(min_value=0, max_value=39))
    @settings(max_examples=100)
    def test_verified_false_range(self, score):
        """
        Property 6: Verified False Range (0-39)
        **Validates: Requirements 4.5**
        
        All scores in the range [0, 39] should map to "Verified False".
        """
        scorer = CredibilityScorer()
        category = scorer._map_score_to_category(score)
        
        assert category == "Verified False", (
            f"Score {score} should map to 'Verified False', got '{category}'"
        )
    
    @given(st.integers(min_value=40, max_value=59))
    @settings(max_examples=100)
    def test_likely_false_range(self, score):
        """
        Property 6: Likely False Range (40-59)
        **Validates: Requirements 4.6**
        
        All scores in the range [40, 59] should map to "Likely False".
        """
        scorer = CredibilityScorer()
        category = scorer._map_score_to_category(score)
        
        assert category == "Likely False", (
            f"Score {score} should map to 'Likely False', got '{category}'"
        )
    
    @given(st.integers(min_value=60, max_value=69))
    @settings(max_examples=100)
    def test_uncertain_range(self, score):
        """
        Property 6: Uncertain Range (60-69)
        **Validates: Requirements 4.7**
        
        All scores in the range [60, 69] should map to "Uncertain".
        """
        scorer = CredibilityScorer()
        category = scorer._map_score_to_category(score)
        
        assert category == "Uncertain", (
            f"Score {score} should map to 'Uncertain', got '{category}'"
        )
    
    @given(st.integers(min_value=70, max_value=84))
    @settings(max_examples=100)
    def test_likely_true_range(self, score):
        """
        Property 6: Likely True Range (70-84)
        **Validates: Requirements 4.8**
        
        All scores in the range [70, 84] should map to "Likely True".
        """
        scorer = CredibilityScorer()
        category = scorer._map_score_to_category(score)
        
        assert category == "Likely True", (
            f"Score {score} should map to 'Likely True', got '{category}'"
        )
    
    @given(st.integers(min_value=85, max_value=100))
    @settings(max_examples=100)
    def test_verified_true_range(self, score):
        """
        Property 6: Verified True Range (85-100)
        **Validates: Requirements 4.9**
        
        All scores in the range [85, 100] should map to "Verified True".
        """
        scorer = CredibilityScorer()
        category = scorer._map_score_to_category(score)
        
        assert category == "Verified True", (
            f"Score {score} should map to 'Verified True', got '{category}'"
        )
    
    @given(st.integers(min_value=0, max_value=100))
    @settings(max_examples=100)
    def test_boundary_values_correctly_mapped(self, score):
        """
        Property 6: Boundary Value Correctness
        **Validates: Requirements 4.5, 4.6, 4.7, 4.8, 4.9**
        
        Boundary values should be correctly assigned to their respective categories.
        This test verifies the exact boundaries: 0, 39, 40, 59, 60, 69, 70, 84, 85, 100.
        """
        scorer = CredibilityScorer()
        category = scorer._map_score_to_category(score)
        
        # Define expected mapping with explicit boundaries
        if score <= 39:
            expected = "Verified False"
        elif score <= 59:
            expected = "Likely False"
        elif score <= 69:
            expected = "Uncertain"
        elif score <= 84:
            expected = "Likely True"
        else:  # score >= 85
            expected = "Verified True"
        
        assert category == expected, (
            f"Score {score} should map to '{expected}', got '{category}'"
        )
    
    def test_specific_boundary_values(self):
        """
        Property 6: Explicit Boundary Testing
        **Validates: Requirements 4.5, 4.6, 4.7, 4.8, 4.9**
        
        Test the exact boundary values to ensure correct category assignment.
        """
        scorer = CredibilityScorer()
        
        # Test lower boundaries
        assert scorer._map_score_to_category(0) == "Verified False"
        assert scorer._map_score_to_category(39) == "Verified False"
        assert scorer._map_score_to_category(40) == "Likely False"
        assert scorer._map_score_to_category(59) == "Likely False"
        assert scorer._map_score_to_category(60) == "Uncertain"
        assert scorer._map_score_to_category(69) == "Uncertain"
        assert scorer._map_score_to_category(70) == "Likely True"
        assert scorer._map_score_to_category(84) == "Likely True"
        assert scorer._map_score_to_category(85) == "Verified True"
        assert scorer._map_score_to_category(100) == "Verified True"
    
    @given(st.integers(min_value=0, max_value=100))
    @settings(max_examples=100)
    def test_mapping_is_deterministic(self, score):
        """
        Property 6: Deterministic Mapping
        **Validates: Requirements 4.5, 4.6, 4.7, 4.8, 4.9**
        
        The same score should always map to the same category (deterministic).
        """
        scorer = CredibilityScorer()
        
        # Map the same score multiple times
        category1 = scorer._map_score_to_category(score)
        category2 = scorer._map_score_to_category(score)
        category3 = scorer._map_score_to_category(score)
        
        assert category1 == category2 == category3, (
            f"Non-deterministic mapping for score {score}:\n"
            f"First call: {category1}\n"
            f"Second call: {category2}\n"
            f"Third call: {category3}"
        )
    
    @given(st.integers(min_value=0, max_value=99))
    @settings(max_examples=100)
    def test_adjacent_scores_in_same_range_have_same_category(self, score):
        """
        Property 6: Adjacent Score Consistency
        **Validates: Requirements 4.5, 4.6, 4.7, 4.8, 4.9**
        
        Adjacent scores within the same range should map to the same category,
        except at boundaries.
        """
        scorer = CredibilityScorer()
        
        category_current = scorer._map_score_to_category(score)
        category_next = scorer._map_score_to_category(score + 1)
        
        # Identify boundary points where category should change
        boundaries = [39, 59, 69, 84]
        
        if score in boundaries:
            # At boundaries, categories should differ
            assert category_current != category_next, (
                f"At boundary {score}, categories should differ:\n"
                f"Score {score}: {category_current}\n"
                f"Score {score + 1}: {category_next}"
            )
        else:
            # Not at boundary, categories should be the same
            assert category_current == category_next, (
                f"Adjacent scores {score} and {score + 1} should have same category:\n"
                f"Score {score}: {category_current}\n"
                f"Score {score + 1}: {category_next}"
            )
    
    @given(st.integers(min_value=0, max_value=100))
    @settings(max_examples=100)
    def test_category_ordering_reflects_score_ordering(self, score):
        """
        Property 6: Category Ordering
        **Validates: Requirements 4.5, 4.6, 4.7, 4.8, 4.9**
        
        Categories should be ordered from most negative to most positive,
        reflecting the score ordering.
        """
        scorer = CredibilityScorer()
        category = scorer._map_score_to_category(score)
        
        # Define category ordering (lower index = more negative)
        category_order = [
            "Verified False",
            "Likely False",
            "Uncertain",
            "Likely True",
            "Verified True"
        ]
        
        category_index = category_order.index(category)
        
        # Property: Higher scores should have higher or equal category index
        if score < 40:
            assert category_index == 0, f"Score {score} should be in category index 0"
        elif score < 60:
            assert category_index == 1, f"Score {score} should be in category index 1"
        elif score < 70:
            assert category_index == 2, f"Score {score} should be in category index 2"
        elif score < 85:
            assert category_index == 3, f"Score {score} should be in category index 3"
        else:
            assert category_index == 4, f"Score {score} should be in category index 4"
    
    @given(
        score1=st.integers(min_value=0, max_value=100),
        score2=st.integers(min_value=0, max_value=100)
    )
    @settings(max_examples=100)
    def test_higher_score_never_gives_lower_category(self, score1, score2):
        """
        Property 6: Monotonic Category Assignment
        **Validates: Requirements 4.5, 4.6, 4.7, 4.8, 4.9**
        
        A higher score should never result in a "lower" (more negative) category
        than a lower score.
        """
        scorer = CredibilityScorer()
        
        category1 = scorer._map_score_to_category(score1)
        category2 = scorer._map_score_to_category(score2)
        
        # Define category ordering
        category_order = [
            "Verified False",
            "Likely False",
            "Uncertain",
            "Likely True",
            "Verified True"
        ]
        
        index1 = category_order.index(category1)
        index2 = category_order.index(category2)
        
        # Property: If score1 < score2, then category index should not decrease
        if score1 < score2:
            assert index1 <= index2, (
                f"Higher score should not give lower category:\n"
                f"Score {score1} -> {category1} (index {index1})\n"
                f"Score {score2} -> {category2} (index {index2})"
            )
        elif score1 > score2:
            assert index1 >= index2, (
                f"Lower score should not give higher category:\n"
                f"Score {score1} -> {category1} (index {index1})\n"
                f"Score {score2} -> {category2} (index {index2})"
            )
        else:  # score1 == score2
            assert index1 == index2, (
                f"Same score should give same category:\n"
                f"Score {score1} -> {category1} (index {index1})\n"
                f"Score {score2} -> {category2} (index {index2})"
            )
    
    @given(st.integers(min_value=0, max_value=100))
    @settings(max_examples=100)
    def test_no_gaps_in_score_range(self, score):
        """
        Property 6: Complete Coverage Without Gaps
        **Validates: Requirements 4.5, 4.6, 4.7, 4.8, 4.9**
        
        Every integer score from 0 to 100 should map to a category with no gaps.
        """
        scorer = CredibilityScorer()
        
        # Should not raise exception
        category = scorer._map_score_to_category(score)
        
        # Should return a valid category
        assert category is not None, f"Score {score} returned None"
        assert isinstance(category, str), f"Score {score} returned non-string: {type(category)}"
        assert len(category) > 0, f"Score {score} returned empty string"
    
    def test_all_categories_are_reachable(self):
        """
        Property 6: All Categories Reachable
        **Validates: Requirements 4.5, 4.6, 4.7, 4.8, 4.9**
        
        All five categories should be reachable by some score in the range [0, 100].
        """
        scorer = CredibilityScorer()
        
        # Collect all categories from all scores
        categories_found = set()
        for score in range(101):
            category = scorer._map_score_to_category(score)
            categories_found.add(category)
        
        expected_categories = {
            "Verified False",
            "Likely False",
            "Uncertain",
            "Likely True",
            "Verified True"
        }
        
        assert categories_found == expected_categories, (
            f"Not all categories are reachable:\n"
            f"Expected: {expected_categories}\n"
            f"Found: {categories_found}\n"
            f"Missing: {expected_categories - categories_found}"
        )
    
    def test_category_ranges_are_correct_size(self):
        """
        Property 6: Category Range Sizes
        **Validates: Requirements 4.5, 4.6, 4.7, 4.8, 4.9**
        
        Verify that each category covers the correct number of score values:
        - Verified False: 40 values (0-39)
        - Likely False: 20 values (40-59)
        - Uncertain: 10 values (60-69)
        - Likely True: 15 values (70-84)
        - Verified True: 16 values (85-100)
        """
        scorer = CredibilityScorer()
        
        # Count scores in each category
        category_counts = {
            "Verified False": 0,
            "Likely False": 0,
            "Uncertain": 0,
            "Likely True": 0,
            "Verified True": 0
        }
        
        for score in range(101):
            category = scorer._map_score_to_category(score)
            category_counts[category] += 1
        
        # Verify expected counts
        assert category_counts["Verified False"] == 40, (
            f"Verified False should cover 40 scores, got {category_counts['Verified False']}"
        )
        assert category_counts["Likely False"] == 20, (
            f"Likely False should cover 20 scores, got {category_counts['Likely False']}"
        )
        assert category_counts["Uncertain"] == 10, (
            f"Uncertain should cover 10 scores, got {category_counts['Uncertain']}"
        )
        assert category_counts["Likely True"] == 15, (
            f"Likely True should cover 15 scores, got {category_counts['Likely True']}"
        )
        assert category_counts["Verified True"] == 16, (
            f"Verified True should cover 16 scores, got {category_counts['Verified True']}"
        )
        
        # Verify total
        total = sum(category_counts.values())
        assert total == 101, f"Total scores should be 101 (0-100), got {total}"
