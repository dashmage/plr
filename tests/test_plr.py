def test_parse_examples(test_runner):
    parsed_result = test_runner.parse_examples()
    assert parsed_result == [['nums = [2,7,11,15], target = 9', '[0,1]']]
