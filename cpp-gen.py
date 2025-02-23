import rsaregex
import argparse
import sys

parser = argparse.ArgumentParser(
                    prog='cpp-gen',
                    description='C++ code generator for a run of a drsa',
                    epilog='')
parser.add_argument('pattern',
                    help='pattern to be matched to input data')

args = parser.parse_args()



print(f"generating drsa for pattern '{args.pattern}'", file=sys.stderr)
drsa = rsaregex.create_rsa(args.pattern)
ordered_regs = list(drsa.R)

#rsaregex.draw_automaton(drsa, "rsa")

# states_i = {item: i + 1 for i, item in enumerate(drsa.Q)}
states_i = {}
i = 0
for s in drsa.Q:
    key = (frozenset(s.states), frozenset(s.mapping.items()))
    states_i[key] = i
    i += 1

init_s = next(iter(drsa.I))
init_i = states_i[(frozenset(init_s.states), frozenset(init_s.mapping.items()))]

final_ind = set()
for f in drsa.F:
    final_ind.add(states_i[(frozenset(f.states), frozenset(f.mapping.items()))])

# for t in drsa.delta:
#     print(t.update  )
# exit()

def compute_trans_bitmap(regs, guardeq):
    bitmap = 0
    i = 0
    for r in regs:
        if r in guardeq:
            bitmap += 1 << i
        i += 1
    return bitmap

def print_reg_update(regs, update):
    spacing = "                    "
    i = 0
    for r in regs:
        print(f"{spacing}std::unordered_set<char32_t> tmp_set_{i};")
        for r2 in regs:
            if r2 in update[r]:
                print(f"{spacing}tmp_set_{i}.insert(regs[{i}].begin(), regs[{i}].end());")
        if 'in' in update[r]:
            print(f"{spacing}tmp_set_{i}.insert(a);")
        i += 1

    i = 0
    for r in regs:
        print(f"{spacing}regs[{i}] = tmp_set_{i};")
        i += 1

# prefix
print('''#include <string>
#include <iostream>
#include <unordered_set>
#include <array>
#include <cstdint>
#include <frozen/unordered_set.h>

#define NUM_REGS ''' + str(len(drsa.R)) +'''
typedef std::array<std::unordered_set<char32_t>, NUM_REGS> regs_t;


char32_t get_next_codepoint(const std::string& utf8_input) {
    static size_t i = 0;
    if (i < utf8_input.size()) {
        char32_t ch = 0;
        unsigned char byte = static_cast<unsigned char>(utf8_input[i]);

        if (byte <= 0x7F) { // 1-byte character
            ch = byte;
            ++i;
        } else if ((byte & 0xE0) == 0xC0) { // 2-byte character
            ch = byte & 0x1F;
            ch = (ch << 6) | (utf8_input[i + 1] & 0x3F);
            i += 2;
        } else if ((byte & 0xF0) == 0xE0) { // 3-byte character
            ch = byte & 0x0F;
            ch = (ch << 6) | (utf8_input[i + 1] & 0x3F);
            ch = (ch << 6) | (utf8_input[i + 2] & 0x3F);
            i += 3;
        } else if ((byte & 0xF8) == 0xF0) { // 4-byte character
            ch = byte & 0x07;
            ch = (ch << 6) | (utf8_input[i + 1] & 0x3F);
            ch = (ch << 6) | (utf8_input[i + 2] & 0x3F);
            ch = (ch << 6) | (utf8_input[i + 3] & 0x3F);
            i += 4;
        } else {
            throw std::runtime_error("Invalid UTF-8 encoding");
        }

        return ch;
    }
    return '\\0';
}

//TODO: generate differently for NUM_REGS > 64
inline uint_fast64_t compute_reg_bitmap(regs_t &regs, char32_t a)
{
    uint_fast64_t bitmap = 0;
    for (size_t i = 0; i < NUM_REGS; i++)
    {
        //assumes contains returns 1 for true
        bitmap += (regs[i].contains(a)) << i;
    }
    return bitmap;
}

inline bool cmp_bitmap(uint_fast64_t a, uint_fast64_t b)
{
    return !(a - b);
}

//FIXME: doesn't work
inline void update_regs(regs_t &regs, char32_t a, uint_fast64_t up_bitmap)
{
    for (size_t i = 0; i < NUM_REGS; i++)
    {
        if ((1 << i) && up_bitmap) {
            regs[i].insert(a);
        }
    }
}
''')

print('''bool run_word(std::string input) {
    int s = '''+ str(init_i) +''';
    std::array<std::unordered_set<char32_t>, NUM_REGS> regs;
    constexpr frozen::unordered_set<uint_fast64_t, ''' + str(len(final_ind)) +'''> final = '''+ str(final_ind) +''';
    char32_t a = get_next_codepoint(input);
    while (a != '\\0') {
        uint_fast64_t a_bitmap = compute_reg_bitmap(regs, a);
        switch (s)
        {''')


for s in states_i.keys():
    s_ind = states_i[s]
    print(f"        case {s_ind}:")
    print("        {")
    cnt = 0
    for t in drsa.trans_dict[s]:
        t_bitmap = compute_trans_bitmap(ordered_regs, t.eqGuard)
        chars_set = set(t.symbol[1])
        cond = "!" if t.symbol[0] == "^" else ""
        set_name = f'trans_chars_{s_ind}_{cnt}'
        if len(chars_set) > 0:
            print('''
                constexpr frozen::unordered_set<char32_t, ''' + str(len(chars_set)) +'> '+set_name+' = '+ str(chars_set) +''';
                if (cmp_bitmap(a_bitmap, (uint_fast64_t)'''+str(t_bitmap)+''') && '''+ cond+set_name+'''.contains(a)) {''')
                    # update_regs(regs, a, (uint_fast64_t)'''+str(t_bitmap)+''');
            print_reg_update(ordered_regs, t.update)
            print('''
                        s ='''+str(states_i[(frozenset(t.dest.states),frozenset(t.dest.mapping.items()))])+''';
                    break;
                }''')
        #not empty set, i.e. every char
        elif cond == "!":
            print('''
                if (cmp_bitmap(a_bitmap, (uint_fast64_t)'''+str(t_bitmap)+''')) {''')
                    #update_regs(regs, a, (uint_fast64_t)'''+str(t_bitmap)+''');
            print_reg_update(ordered_regs, t.update)                    
            print('''
                    s ='''+str(states_i[(frozenset(t.dest.states),frozenset(t.dest.mapping.items()))])+''';
                    break;
                }''')
        cnt += 1
    print("            return false;")
    print("        }")

print('''        default:
            break;
        }
        a = get_next_codepoint(input);
    }
    if (final.contains(s)) {
        return true;
    }
    return false;
}''')

print('''

int main(int argc, char *argv[]) {
    if (argc != 2) {
        printf("Missing argument\\n");
        return 1;
    }
    std::string input = argv[1];
    bool result = run_word(input);
    if (result) printf("YES\\n");
    else printf("NO\\n");
}''')
