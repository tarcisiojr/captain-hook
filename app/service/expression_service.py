from app.service.extensions.evaluate_expression import pyparsing_engine


def evaluate(expression, variables):
    return pyparsing_engine.evaluate(expression, variables)