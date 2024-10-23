from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
import re
from bson.objectid import ObjectId

app = Flask(__name__)

# MongoDB Setup (Change to your connection details)
client = MongoClient("mongodb://localhost:27017/")
db = client['rule_engine_db']
rules_collection = db['rules']

# Define the Node structure for the AST
class Node:
    def __init__(self, node_type, left=None, right=None, value=None):
        self.type = node_type  # "operator" or "operand"
        self.left = left  # left child (Node)
        self.right = right  # right child (Node)
        self.value = value  # condition value, e.g., number or string

# Tokenization and parsing functions
def create_rule(rule_string):
    tokens = tokenize(rule_string)
    return parse(tokens)

def tokenize(rule_string):
    return re.findall(r'\(|\)|AND|OR|>|<|=|\w+|\'[\w\s]+\'|\d+', rule_string)

def parse(tokens):
    if len(tokens) == 1:
        return Node("operand", value=tokens[0])
    
    stack = []
    current = None
    
    while tokens:
        token = tokens.pop(0)
        
        if token == '(':
            stack.append(current)
            current = None
        elif token == ')':
            temp = current
            current = stack.pop()
            if current:
                if not current.left:
                    current.left = temp
                else:
                    current.right = temp
            else:
                current = temp
        elif token in ("AND", "OR"):
            new_node = Node("operator", value=token)
            new_node.left = current
            current = new_node
        else:
            if not current:
                current = Node("operand", value=token)
            elif current.type == "operator":
                current.right = Node("operand", value=token)
    return current

# Evaluate the AST against user data
def evaluate_rule(ast, data):
    if ast.type == "operand":
        return eval_condition(ast.value, data)
    
    if ast.type == "operator":
        if ast.value == "AND":
            return evaluate_rule(ast.left, data) and evaluate_rule(ast.right, data)
        elif ast.value == "OR":
            return evaluate_rule(ast.left, data) or evaluate_rule(ast.right, data)

def eval_condition(condition, data):
    match = re.match(r'(\w+)\s*(>|<|=)\s*(\w+)', condition)
    if not match:
        return False
    
    key, operator, value = match.groups()
    value = int(value) if value.isdigit() else value.strip("'")
    
    if operator == '>':
        return data.get(key, 0) > value
    elif operator == '<':
        return data.get(key, 0) < value
    elif operator == '=':
        return data.get(key) == value

# API to create and store a rule
@app.route('/create_rule', methods=['POST'])
def create_rule_api():
    rule_string = request.json['rule']
    rule_ast = create_rule(rule_string)
    
    # Store rule in MongoDB
    rule_doc = {
        'rule_string': rule_string,
        'rule_ast': serialize_ast(rule_ast)
    }
    result = rules_collection.insert_one(rule_doc)
    
    return jsonify({'message': 'Rule created successfully', 'rule_id': str(result.inserted_id)}), 201

# API to evaluate a rule
@app.route('/evaluate_rule/<rule_id>', methods=['POST'])
def evaluate_rule_api(rule_id):
    user_data = request.json
    rule_doc = rules_collection.find_one({'_id': ObjectId(rule_id)})
    
    if not rule_doc:
        return jsonify({'message': 'Rule not found'}), 404
    
    rule_ast = deserialize_ast(rule_doc['rule_ast'])
    result = evaluate_rule(rule_ast, user_data)
    
    return jsonify({'result': result})

# Helper functions to serialize/deserialize AST for MongoDB storage
def serialize_ast(ast):
    if not ast:
        return None
    return {
        'type': ast.type,
        'value': ast.value,
        'left': serialize_ast(ast.left),
        'right': serialize_ast(ast.right)
    }

def deserialize_ast(data):
    if not data:
        return None
    return Node(data['type'], deserialize_ast(data['left']), deserialize_ast(data['right']), data['value'])

# Simple UI for creating rules
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
