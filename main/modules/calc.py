# meta developer: @znxiw
# да я вообще не вкуриваю что тут за хуйня
# бухой написал

import ast
import operator
from .. import loader, utils

__version__ = (1, 0, 0)

_OP_MAP = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

# защита от хуесосов, которые лярды нахуй на 9999999999999 умножают
class Calculator(ast.NodeVisitor):
    """Безопасный обработчик арифметических выражений."""

    def visit_BinOp(self, node):
        """Обрабатывает бинарные операции (x + y)."""
        left = self.visit(node.left)
        right = self.visit(node.right)

        op_func = _OP_MAP.get(type(node.op))
        if op_func is None:
            raise TypeError(f"Неподдерживаемый оператор: {type(node.op).__name__}")
        
        if type(node.op) is ast.Pow and right > 100:
             raise ValueError("Слишком большая степень")

        return op_func(left, right)

    def visit_UnaryOp(self, node):
        """Обрабатывает унарные операции (-x, +x)."""
        operand = self.visit(node.operand)
        op_func = _OP_MAP.get(type(node.op))
        if op_func is None:
            raise TypeError(f"Неподдерживаемый унарный оператор: {type(node.op).__name__}")
        return op_func(operand)

    def visit_Num(self, node):
        """Обрабатывает числа."""
        return node.n

    def visit_Constant(self, node):
        """Обрабатывает константы в Python 3.8+."""
        if isinstance(node.value, (int, float)):
            return node.value
        raise TypeError(f"Неподдерживаемая константа: {type(node.value).__name__}")

    def generic_visit(self, node):
        """Отклоняет все остальные узлы, такие как вызовы функций, переменные и т. д."""
        if isinstance(node, (ast.Expression, ast.Module)):
            return super().generic_visit(node)
        
        raise TypeError(f"Неподдерживаемый синтаксис: {type(node).__name__}")

def safe_eval(expression):
    """Парсит и безопасно вычисляет выражение."""
    if len(expression) > MAX_COMPLEXITY:
        raise ValueError("Слишком длинное выражение")
        
    tree = ast.parse(expression, mode='eval')
    
    return Calculator().visit(tree.body)


class КукуляторMod(loader.Module):
    """Кукулирует выражения"""
    strings = {'name': 'Кукулятор'}
    
    async def calccmd(self, message):
        """.calc <выражение или реплай на то, что нужно посчитать>
            Кстати:
            ** - возвести в степень
            / - деление
            % - деление по модулю"""
        
        question = utils.get_args_raw(message)
        
        if not question:
            reply_text = await utils.get_reply_text(message)
            if not reply_text:
                await utils.answer(message, "<b>2+2=5</b>")
                return
            question = reply_text
            
        try:
            answer = safe_eval(question)
            
            if isinstance(answer, (int, float)):
                formatted_answer = f"{answer:g}"
            else:
                formatted_answer = str(answer)
                
            final_answer = f"<b>{question}=</b><code>{formatted_answer}</code>"
        
        except Exception as e:
            error_message = str(e).splitlines()[0] if str(e) else "Неизвестная ошибка вычисления"
            final_answer = f"<b>{question}=</b><code>Ошибка: {error_message}</code>"
            
        await utils.answer(message, final_answer)