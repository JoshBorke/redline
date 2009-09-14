from decimal import Decimal
from django import template
from django.conf import settings


register = template.Library()

# To override, copy to your settings file. Make sure to keep the tuples in
# descending order by percentage.
BUDGET_DEFAULT_COLORS = (
    # (percentage, CSS color class)
    (1.001, 'red'),
    (0.75, 'yellow'),
    (0.0, 'green'),
)


class ColorizeAmountNode(template.Node):
    def __init__(self, estimated_amount, actual_amount):
        self.estimated_amount = template.Variable(estimated_amount)
        self.actual_amount = template.Variable(actual_amount)

    def render(self, context):
        if hasattr(settings, 'BUDGET_DEFAULT_COLORS'):
            colors = settings.BUDGET_DEFAULT_COLORS
        else:
            colors = BUDGET_DEFAULT_COLORS

        try:
            estimate = self.estimated_amount.resolve(context)
            actual = self.actual_amount.resolve(context)
            estimate = make_decimal(estimate)
            actual = make_decimal(actual)
            percentage = actual / estimate

            for color in colors:
                color_percentage = make_decimal(color[0])

                if percentage >= color_percentage:
                    return color[1]
        except template.VariableDoesNotExist:
            return ''


def make_decimal(amount):
    """
    If it's not a Decimal, it should be...
    """
    if not isinstance(amount, Decimal):
        amount = Decimal(str(amount))

    return amount


def colorize_amount(parser, token):
    """
    Compares an estimate with an actual amount and returns an appropriate
    color as a visual indicator.

    Example:

        {% colorize_amount estimated_amount actual_amount %}
    """
    try:
        tag_name, estimated_amount, actual_amount = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires exactly two arguments" % token.contents.split()[0])
    return ColorizeAmountNode(estimated_amount, actual_amount)

class ColorizeBudgetNode(template.Node):
    def __init__(self, budget_str, start_date_str, end_date_str):
        self.budget = template.Variable(budget_str)
        self.start_date = template.Variable(start_date_str)
        self.end_date = template.Variable(end_date_str)

    def render(self, context):
        b = self.budget.resolve(context)
        start = self.start_date.resolve(context)
        end = self.end_date.resolve(context)
        estimated_amount = b.amount
        amount_used = b.actual_total(start, end)
        if hasattr(settings, 'BUDGET_DEFAULT_COLORS'):
            colors = settings.BUDGET_DEFAULT_COLORS
        else:
            colors = BUDGET_DEFAULT_COLORS

        try:
            estimate = b.amount
            actual = b.actual_total(start, end)
            estimate = make_decimal(estimate)
            actual = make_decimal(actual)
            percentage = actual / estimate

            for color in colors:
                color_percentage = make_decimal(color[0])

                if percentage >= color_percentage:
                    return color[1]
        except template.VariableDoesNotExist:
            return ''

def colorize_budget(parser, token):
    """
    Compares an estimate with an actual amount and returns an appropriate
    color as a visual indicator.

    Example:

        {% colorize_amount estimated_amount actual_amount %}
    """
    try:
        tag_name, budget, start_date, end_date = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires exactly three arguments" % token.contents.split()[0])
    return ColorizeBudgetNode(budget, start_date, end_date)


class ProgressBarNode(template.Node):
    def __init__(self, budget_str, start_date_str, end_date_str):
        self.budget = template.Variable(budget_str)
        self.start_date = template.Variable(start_date_str)
        self.end_date = template.Variable(end_date_str)

    def render(self, context):
        b = self.budget.resolve(context)
        start = self.start_date.resolve(context)
        end = self.end_date.resolve(context)
        estimated_amount = b.amount
        amount_used = b.actual_total(start, end)
        progress_bar_percent = int(amount_used / estimated_amount * 100)

        if progress_bar_percent >= 100:
            progress_bar_percent = 100
        return str(progress_bar_percent)

def progress_bar_width(parser, token):
    """
    Compares an estimate with an actual amount and returns an appropriate
    color as a visual indicator.

    Example:

        {% colorize_amount estimated_amount actual_amount %}
    """
    try:
        tag_name, budget, start_date, end_date = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires exactly three arguments" % token.contents.split()[0])
    return ProgressBarNode(budget, start_date, end_date)


class BudgetInfoNode(template.Node):
    def __init__(self, budget_str, start_date_str, end_date_str):
        self.budget = template.Variable(budget_str)
        self.start_date = template.Variable(start_date_str)
        self.end_date = template.Variable(end_date_str)

    def render(self, context):
        b = self.budget.resolve(context)
        start = self.start_date.resolve(context)
        end = self.end_date.resolve(context)
        estimated_amount = b.amount
        amount_used = b.actual_total(start, end)
        res = b.name + ": " + str(amount_used) + " out of " + str(estimated_amount) + " used."
        return res

def budget_info(parser, token):
    try:
        tag_name, budget, start_date, end_date = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires exactly three arguments" % token.contents.split()[0])
    return BudgetInfoNode(budget, start_date, end_date)

register.tag('colorize_amount', colorize_amount)
register.tag('colorize_budget', colorize_budget)
register.tag('progress_bar_width', progress_bar_width)
register.tag('budget_info', budget_info)

def budget_month_summary(context):
    budget = context['budget']
    start_date = context['start_date']
    end_date = context['end_date']
    transactions = budget.actual_transactions(start_date, end_date)
    actual_amount = budget.actual_amount(start_date, end_date)
    return {
        'budget' : budget,
        'transactions' : transactions,
        'actual_amount' : actual_amount
    }
register.inclusion_tag('budget/summaries/budget_summary_month.html', takes_context=True)(budget_month_summary)

def budget_year_summary(context):
    budget = context['budget']
    start_date = context['start_date']
    end_date = context['end_date']
    transactions = budget.actual_transactions(start_date, end_date)
    actual_amount = budget.actual_amount(start_date, end_date)
    return {
        'budget' : budget,
        'transactions' : transactions,
        'actual_amount' : actual_amount
    }
register.inclusion_tag('budget/summaries/budget_summary_year.html', takes_context=True)(budget_year_summary)
