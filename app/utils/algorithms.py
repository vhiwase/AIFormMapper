import difflib
from typing import List, Tuple, Dict

__all__ = ['get_string_similarity']


def get_string_differences(source_text: str, target_text: str) -> List[Tuple[str, str, str, int, int]]:
    """
    Compare two strings and return their differences using SequenceMatcher.
    Case sensitive comparison.
    
    Args:
        source_text: The source string to compare from
        target_text: The target string to compare against
        
    Returns:
        List of tuples containing (operation_type, source_substring, target_substring, source_start, target_start)
        where operation_type can be 'equal', 'replace', 'delete', or 'insert'
    """
    # Create a new sequence matcher with case-sensitive comparison
    sequence_matcher = difflib.SequenceMatcher(lambda x: False, source_text, target_text)
    diff_results = []
    for op_type, src_start, src_end, tgt_start, tgt_end in sequence_matcher.get_opcodes():
        diff_results.append((op_type, source_text[src_start:src_end], 
                          target_text[tgt_start:tgt_end], src_start, tgt_start))
    return diff_results


def get_string_similarity(main_text: str, search_text: str) -> Dict:
    """
    Calculate similarity metrics between a text and a subtext.
    Case sensitive comparison.
    
    Args:
        main_text: The main text to compare against
        search_text: The substring to find similarity metrics for
        
    Returns:
        Dictionary containing similarity metrics:
            - dissimilarity_score: Combined score of differences (lower is better)
            - text_length: Total length of the main text
            - subtext_length: Total length of the subtext
            - unmatched_char_count: Number of characters that don't match exactly
            - matched_char_count: Number of characters that match exactly
            - gap_char_count: Number of characters in gaps between matches
            - inserted_char_count: Number of extra characters
            - replaced_char_count: Number of replaced characters
            - matches: List of matching text segments
            - replacements: List of tuples containing (original_text, replacement_text)
            - gaps: List of gap text segments
    """
    text_segments = []

    for op_type, src_segment, tgt_segment, src_idx, tgt_idx in get_string_differences(main_text, search_text):
        if op_type in ['equal', 'replace', 'insert']:
            text_segments.append((op_type, (src_idx, src_idx + len(src_segment)), (tgt_idx, tgt_idx + len(tgt_segment))))

    # Sort by start index
    text_segments.sort(key=lambda x: x[1][0])
    
    # Find unmatched segments in text
    unmatched_ranges = []
    for idx in range(len(text_segments) - 1):
        current_end = text_segments[idx][1][1]
        next_start = text_segments[idx + 1][1][0]
        if current_end < next_start:
            unmatched_ranges.append((current_end, next_start))
    
    # Collect matching segments with actual text
    exact_matches = [main_text[range_start:range_end] 
                    for op_type, (range_start, range_end), _ in text_segments if op_type == 'equal']
    
    # Collect replacement segments with actual text pairs
    replacements = [(main_text[range_start:range_end], search_text[search_range[0]:search_range[1]]) 
                   for op_type, (range_start, range_end), search_range in text_segments if op_type == 'replace']
    
    # Collect gaps with actual text
    gaps = [main_text[start:end] for start, end in unmatched_ranges]
    
    # Calculate metrics
    gap_sizes = [(gap[1]-gap[0]) for gap in unmatched_ranges]
    total_gap_chars = sum(gap_sizes)

    match_sizes = [(segment[2][1] - segment[2][0]) 
                  for segment in text_segments if segment[0]=='equal']
    total_matched_chars = sum(match_sizes)

    insertion_sizes = [(segment[2][1] - segment[2][0]) 
                      for segment in text_segments if segment[0]=='insert']
    total_inserted_chars = sum(insertion_sizes)

    replacement_sizes = [(segment[1][1]-segment[1][0]) 
                        for segment in text_segments if segment[0]=='replace']
    total_replaced_chars = sum(replacement_sizes)
    
    main_text_length = len(main_text)
    search_text_length = len(search_text)
    total_unmatched_chars = (search_text_length - total_matched_chars)
    
    dissimilarity_score = (total_unmatched_chars + 
                          total_inserted_chars + 
                          total_replaced_chars + 
                          total_gap_chars)
    
    return {
        'dissimilarity_score': dissimilarity_score,
        'text_length': main_text_length,
        'subtext_length': search_text_length,
        'unmatched_char_count': total_unmatched_chars,
        'matched_char_count': total_matched_chars,
        'gap_char_count': total_gap_chars,
        'inserted_char_count': total_inserted_chars,
        'replaced_char_count': total_replaced_chars,
        'matches': exact_matches,
        'replacements': replacements,
        'gaps': gaps
    }


def display_comparison_details(main_text: str, search_text: str, comparison_results: Dict):
    """Helper function to print detailed comparison results."""
    print("\nInput Strings:")
    print(f"Text    : '{main_text}'")
    print(f"Subtext : '{search_text}'")
    
    print("\nMetrics:")
    for metric_name, metric_value in comparison_results.items():
        print(f"{metric_name:<20}: {metric_value}")


def run_examples():
    """Run examples demonstrating string matching behavior with different scenarios."""
    
    print("\n" + "=" * 80)
    print("1. Basic Exact Match")
    print("=" * 80)
    main_text = "Hello World! This is a test string."
    search_text = "This is"
    comparison_results = get_string_similarity(main_text, search_text)
    display_comparison_details(main_text, search_text, comparison_results)

    print("\n" + "=" * 80)
    print("2. Case Sensitivity Example")
    print("=" * 80)
    main_text = "HELLO WORLD! This is a TEST string."
    search_text = "hello world"
    comparison_results = get_string_similarity(main_text, search_text)
    display_comparison_details(main_text, search_text, comparison_results)

    print("\n" + "=" * 80)
    print("3. Partial Match with Special Characters")
    print("=" * 80)
    main_text = "User ID: #12345 (active) - user@example.com"
    search_text = "#12345 - user@example"
    comparison_results = get_string_similarity(main_text, search_text)
    display_comparison_details(main_text, search_text, comparison_results)

    print("\n" + "=" * 80)
    print("4. Whitespace Handling")
    print("=" * 80)
    main_text = "The    quick    brown    fox"
    search_text = "quick brown fox"
    comparison_results = get_string_similarity(main_text, search_text)
    display_comparison_details(main_text, search_text, comparison_results)

    print("\n" + "=" * 80)
    print("5. Multi-line Text")
    print("=" * 80)
    main_text = """First line of text
    Second line with important data
    Third line here"""
    search_text = "Second line with data"
    comparison_results = get_string_similarity(main_text, search_text)
    display_comparison_details(main_text, search_text, comparison_results)

    print("\n" + "=" * 80)
    print("6. Unicode and Emoji")
    print("=" * 80)
    main_text = "Hello 👋 World! 🌍 Have a Nice Day! ⭐"
    search_text = "World! 🌍"
    comparison_results = get_string_similarity(main_text, search_text)
    display_comparison_details(main_text, search_text, comparison_results)


if __name__ == '__main__':
    run_examples()