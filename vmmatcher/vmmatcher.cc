#include <cstdint>
#include <cstddef>
#include <vector>
#include <string>
#include <fstream>
#include <sstream>
#include <iostream>
#include <unordered_set>

#include <ctime>

#include "json.hpp"
using json = nlohmann::json;

using SetImpl = std::unordered_set<uint32_t>;

void debug_print(std::string message) {
    std::cerr << message << "\n";
}

#define BYTES(IN) ((uint8_t *) &IN)
#define NEXT_UNDEFINED (size_t)-2
#define NO_JUMPS (size_t)-1

enum Opcode : uint8_t {
    OP_DECODE,
    OP_UPDATE,
    OP_TEST,
    OP_JUMP,
    OP_ACCEPT,
    OP_FAIL,
};

Opcode parse_opcode(const std::string& s)
{
    if (s == "DECODE") return Opcode::OP_DECODE;
    if (s == "UPDATE")    return Opcode::OP_UPDATE;
    if (s == "TEST")   return Opcode::OP_TEST;
    if (s == "JUMP")   return Opcode::OP_JUMP;
    if (s == "ACCEPT") return Opcode::OP_ACCEPT;
    if (s == "FAIL")   return Opcode::OP_FAIL;

    throw std::runtime_error("unknown opcode");
}

typedef uint16_t reg_t;

struct Instruction {
    Opcode op; // operator
    reg_t reg; // register operand (upd, test)
    size_t ls; // label (jump, test) or state (decode)
    std::vector<reg_t> reg_list; // reglist of upd
};

struct DecodeTreeNode {
    std::vector<DecodeTreeNode*> children;
    size_t label; 
};

void parse_code(std::string filename, std::vector<Instruction> &program) 
{
    std::string line;
    std::ifstream file(filename);
    if (!file.is_open())
        std::cerr << "failed to open " << filename << '\n';

    while (std::getline(file, line)) {
        std::istringstream iss(line);
        std::string word;

        // skip empty line
        if (!(iss >> word)) {
            std::cerr << "skipped line\n";
            continue;
        }
        

        // first word is opcode
        Opcode opcode = parse_opcode(word);
        Instruction inst = {.op = opcode};
        switch (opcode)
        {
        case OP_DECODE:
            if (!(iss >> word))
                throw std::runtime_error("DECODE: missing operand");
            inst.ls = std::stoul(word);
            break;
        
        case OP_UPDATE:
            if (!(iss >> word))
                throw std::runtime_error("UPD: missing operand");
            inst.reg = std::stoul(word);
            for (size_t i = 0; iss >> word; ++i) {
                (inst.reg_list).push_back(std::stoul(word));
            }
            break;

        case OP_TEST:
            if (!(iss >> word))
                throw std::runtime_error("TEST: missing operand");
            inst.reg = std::stoul(word);

            if (!(iss >> word))
                throw std::runtime_error("TEST: missing operand");
            inst.ls = std::stoul(word);
            break;
        
        case OP_JUMP:
            if (!(iss >> word))
                throw std::runtime_error("JUMP: missing operand");
            inst.ls = std::stoul(word);
            break;

        // no additional arguments
        case OP_ACCEPT: break;
        case OP_FAIL: break;
        }

        program.push_back(inst);

        // while (iss >> word) {
        //     std::cout << "word:'" << word << "' ";
        // }
        // std::cout << "\n";
    }
}

size_t traverse_decode_tree(const DecodeTreeNode* node, const uint32_t in, const uint8_t index)
{
    if (node == nullptr)
        return (size_t)-2;
    if (node->children.size() == 0)
        return node->label;
    uint8_t byte = BYTES(in)[index];
    // TODO: once I have bytemap:
    // uint8_t byte = bytemap[BYTES(in)[index]]
    return traverse_decode_tree(node->children[byte], in, index-1);
}

void free_tree(DecodeTreeNode* node)
{
    if (!node) return;

    for (auto* child : node->children) {
        free_tree(child);
    }
    delete node;
}

DecodeTreeNode* deserialize(const json& j)
{
    if (j.is_null()) {
        return nullptr;
    }

    auto* node = new DecodeTreeNode();

    if (j.contains("label") && !j["label"].is_null()) {
        node->label = j["label"].get<size_t>();
    }

    if (j.contains("children")) {
        const auto& j_children = j["children"];
        node->children.resize(j_children.size(), nullptr);

        for (size_t i = 0; i < j_children.size(); ++i) {
            if (!j_children[i].is_null()) {
                node->children[i] = deserialize(j_children[i]);
            }
        }
    }

    return node;
}

std::vector<DecodeTreeNode*> parse_memory(const std::string& filename)
{
    std::ifstream f(filename);
    json j;
    f >> j;

    std::vector<DecodeTreeNode*> forest;
    forest.reserve(j.size());

    for (const auto& tree_json : j) {
        forest.push_back(deserialize(tree_json));
    }

    return forest;
}

bool get_input_char(std::istream& input, char &out)
{
    return (bool)input.get(out); //(bool) tell linter that it's fine :)
}

std::vector<SetImpl> init_regs(const reg_t nregs)
{
    return std::vector<SetImpl>(nregs);
}

uint8_t get_num_bytes(char c)
{
    uint8_t masked = c & 0b11110000;
    if (masked == 0b11110000)
        return 4;
    if (masked >= 0b11100000)
        return 3;
    if (masked >= 0b11000000)
        return 2;
    return 1; 
}


//FIXME: ai generated dump function

void dump_regs(const std::vector<SetImpl>& regs)
{
    for (std::size_t i = 0; i < regs.size(); ++i)
    {
        std::cerr << "Register[" << i << "]: ";

        if (regs[i].empty())
        {
            std::cerr << "{}\n";
            continue;
        }

        std::cerr << "{ ";
        bool first = true;

        for (const auto& value : regs[i])
        {
            if (!first)
                std::cerr << ", ";

            std::cerr << value;
            first = false;
        }

        std::cerr << " }\n";
    }
}
//FIXME: end of ai generated dump function


bool run_code(const std::vector<Instruction> &program,
    const std::vector<DecodeTreeNode*> decodeTrees,
    const reg_t nregs, 
    std::istream& input)
{
    // +1 regs for in, which is regs[0]
    auto regs = init_regs(nregs+1);
    auto regs_new = init_regs(nregs+1);
    uint32_t in = 0;
    size_t ip = 0;
    Instruction instr;
    char curr_byte = 0;
    uint8_t nbytes;
    DecodeTreeNode *tree;
    size_t label;
    bool updated_regs = false;
    while (1) {
        // std::cerr << ip << ":";
        instr = program[ip];
        switch (instr.op)
        {
        case OP_DECODE:
            //debug_print("DECODE");
            in = 0;
            if (updated_regs) {
                //debug_print("REGS UPDATED!");
                std::swap(regs, regs_new);
                updated_regs = false;
                //dump_regs(regs);
            }
            tree = decodeTrees[instr.ls];
            // read first byte
            if (!get_input_char(input, curr_byte)) {
                //debug_print("no input -> fail");
                return false;
            }

            nbytes = get_num_bytes(curr_byte);
            BYTES(in)[0] = curr_byte;

            // get remaining bytes
            for (uint8_t i = 1; i < nbytes; i++)
            {
                assert(get_input_char(input, curr_byte));
                BYTES(in)[i] = curr_byte;
            }
            regs[0].insert(in); // add in to the reg

            //std::cerr << "\t" << in << "\n";

            // get next state
            label = traverse_decode_tree(tree, in, nbytes-1);
            if (label == NEXT_UNDEFINED)
                return false;
            if (label == NO_JUMPS)
                ip++;
            else
                ip = label;

            break;
        
        case OP_ACCEPT:
            //debug_print("ACCEPT");
            if (input.peek() == EOF) {
                //debug_print("\tYES");
                return true;
            }
            //debug_print("\tNO");
            ip++;
            break;

        case OP_FAIL:
            //debug_print("FAIL");
            return false;

        case OP_JUMP:
            //debug_print("JUMP");
            //std::cerr << "\tto " << instr.ls << "\n"; 
            ip = instr.ls;
            break;

        case OP_TEST:
            //debug_print("TEST");
            //std::cerr << "\t" <<  in << " \\in " << instr.reg << "\n"; 
            if (regs[instr.reg].contains(in)) {
                //debug_print("\tYES");
                ip = instr.ls;
                break;
            }
            ip++;
            break;

        case OP_UPDATE:
            //debug_print("UPDATE");
            regs_new[instr.reg].clear();
            for (auto &r : instr.reg_list) {
                regs_new[instr.reg].insert(regs[r].begin(), regs[r].end()); 
            }
            updated_regs = true;
            ip++;
            break;
        }
    } 
}

///////////////////////////////////////////////////////////////////////////////////////////////////////////////
// FIXME: remove later start
///////////////////////////////////////////////////////////////////////////////////////////////////////////////
std::string opcode_to_string(Opcode op) {
    switch (op) {
        case Opcode::OP_DECODE: return "DECODE";
        case Opcode::OP_UPDATE: return "UPDATE";
        case Opcode::OP_TEST:   return "TEST";
        case Opcode::OP_JUMP:   return "JUMP";
        case Opcode::OP_ACCEPT: return "ACCEPT";
        case Opcode::OP_FAIL:   return "FAIL";
        default:                return "UNKNOWN";
    }
}

// Print a single instruction
void print_instruction(const Instruction& inst) {
    std::cout << opcode_to_string(inst.op);

    // Print register operand if applicable
    if (inst.op == Opcode::OP_UPDATE || inst.op == Opcode::OP_TEST) {
        std::cout << " r" << inst.reg;
    }

    // Print label/state for JUMP, TEST, DECODE
    if (inst.op == Opcode::OP_JUMP || inst.op == Opcode::OP_TEST || inst.op == Opcode::OP_DECODE) {
        std::cout << " " << inst.ls;
    }

    // Print reg_list for UPD
    if (inst.op == Opcode::OP_UPDATE && !inst.reg_list.empty()) {
        for (reg_t r : inst.reg_list) {
            std::cout << " r" << r;
        }
    }

    std::cout << "\n";
}

// Print a whole program
void print_program(const std::vector<Instruction>& program) {
    for (size_t i = 0; i < program.size(); ++i) {
        std::cout << i << ": ";
        print_instruction(program[i]);
    }
}

void dump_tree(const DecodeTreeNode* node, int depth = 0, int index = -1) {
    if (!node) {
        std::cout << std::string(depth * 2, ' ')
                  << "[" << index << "] nullptr\n";
        return;
    }

    std::cout << std::string(depth * 2, ' ')
              << "[" << index << "] label="
              << (node->label)
              << "\n";

    for (size_t i = 0; i < node->children.size(); ++i) {
        if (node->children[i]) {
            dump_tree(node->children[i], depth + 1, i);
        } else {
            // std::cout << std::string((depth + 1) * 2, ' ') << "[" << i << "] null\n";
        }
    }
}

void dump_forest(const std::vector<DecodeTreeNode*>& forest) {
    for (size_t i = 0; i < forest.size(); ++i) {
        std::cout << "Tree " << i << ":\n";
        dump_tree(forest[i], 1, -1);
    }
}

///////////////////////////////////////////////////////////////////////////////////////////////////////////////
// FIXME: remove later end
///////////////////////////////////////////////////////////////////////////////////////////////////////////////

int main(int argc, char const *argv[])
{
    if (argc < 2) { //FIXME: interface
        std::cerr << "Missing code file" << "\n";
        return 1;
    }
    std::vector<Instruction> program;
    //std::cerr << "Parsing code..." << "\n";
    parse_code(argv[1], program);
    //std::cerr << "Parsing memory..." << "\n";
    auto forest = parse_memory(argv[2]);
    reg_t nregs = std::stoul(argv[3]);
    // print_program(program);
    // dump_forest(forest);
    //std::cerr << "Code start..." << "\n";
    std::clock_t t0 = std::clock();
    bool ret = run_code(program, forest, nregs, std::cin);
    std::clock_t t1 = std::clock();
    double matchtime = double(t1 - t0) / CLOCKS_PER_SEC;
    std::cout << matchtime;
    if (ret)
        return 0;
    return 1;
}


