# Archived Test Files

These test files have been consolidated into the new organized test suite.

## What was consolidated:

- `test_chat_setup.py` → Configuration tests in `tests/test_chat_system.py`
- `test_complex_queries.py` → Query testing in `tests/test_chat_system.py`
- `test_database_execution.py` → Database integration tests in `tests/test_chat_system.py`
- `test_final_demo.py` → End-to-end tests in `tests/test_chat_system.py`
- `test_fixes_verification.py` → Error handling tests in `tests/test_chat_system.py`
- `test_flexible_intent_detection.py` → Intent detection tests in `tests/test_chat_system.py`
- `test_intent_patterns.py` → Pattern matching tests in `tests/test_chat_system.py`
- `test_nlp_accuracy_fixes.py` → NLP accuracy tests in `tests/test_chat_system.py`
- `test_question_classification.py` → Classification tests in `tests/test_chat_system.py`
- `test_sql_generation.py` → SQL generation tests in `tests/test_chat_system.py`
- `simple_intent_test.py` → Intent testing in `tests/test_chat_system.py`
- `standalone_sql_test.py` → SQL testing in `tests/test_chat_system.py`

## New Structure:

Use `python run_tests.py` to run the consolidated test suite.

The new test structure is:
- `tests/test_chat_system.py` - Comprehensive chat system tests
- `run_tests.py` - Test runner script

This provides better organization, reduces duplication, and makes testing more maintainable.