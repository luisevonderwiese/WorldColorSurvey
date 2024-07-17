import os
import pandas as pd
import string
from colorspacious import cspace_converter
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from multiset import *

def mix_colors(colors):
    concentration = 1.0 / len(colors)
    color = [v * concentration for v in colors[0]]
    for next_color in colors[1:]:
        for i, v in enumerate(next_color):
            color[i] += concentration * v
    return color

def blend_colors(colors_to_blend):
    white_concentration = 1.0
    for color, concentration in colors_to_blend:
        white_concentration -= concentration
    color = [white_concentration, white_concentration, white_concentration]
    for next_color, concentration in colors_to_blend:
        for i, v in enumerate(next_color):
            color[i] += concentration * v
    return color

#build munsell chart data structures
code_to_coord = {}
df = pd.read_csv("cnum-vhcm-lab-new.txt", sep = "\t")
matrix = [[[] for _ in range(42)] for __ in range(11)]
for i, row in df.iterrows():
    lightness = string.ascii_uppercase.index(row["V"])
    hue = row["H"]
    lab = [row["L*"], row["a*"], row["b*"]]
    rgb = cspace_converter("CIELab", "sRGB1")(lab)
    print(lab)
    print(rgb)
    rgb = [max(v, 0) for v in rgb]
    rgb = [min(v, 1) for v in rgb]
    matrix[lightness][hue] = rgb
    code_to_coord[row["#cnum"]] = (lightness, hue)
for hue in range(1, 42):
    matrix[0][hue] = matrix[0][0]
    matrix[9][hue] = matrix[9][0]

#print munsell chart
fig,ax = plt.subplots(figsize=(21, 5))
for lightness, r in enumerate(matrix):
    for hue, value in enumerate(r):
        if len(value) == 0:
            continue
        rect = patches.Rectangle((0.025 * hue, 0.1 * lightness), 0.025, 0.1, linewidth=0, facecolor=value)
        ax.add_patch(rect)
ax.set_axis_off()
plt.savefig("munsell.png")
plt.clf()
plt.close()

#load data
term_df = pd.read_csv("term.txt", sep = "\t") # original data
#term_df = pd.read_csv("gjtermCleaned.txt", sep = " ") # data cleaned with procedure described by Gerhard in his paper
lang_df = pd.read_csv("lang.txt", sep = "\t")
dict_df = pd.read_csv("dict.txt", sep = "\t")
term_df = pd.merge(term_df, lang_df, how = 'left', left_on="#LNUM", right_on = "#LNUM")
term_df = pd.merge(term_df, dict_df, how = 'left', left_on=["#LNUM", "WCSC"], right_on = ["#LNUM", "WCSC"])
print(term_df)

mix_threshold = 0.5 #proportion of consultants which need to agree in one term for a chip to be taken into account for this term
num_blend = 1 #how many colors to blend into each other if results are unclear
fade = False #faded colors for color chips with mixed/unclear results




languages = list(set(term_df["name"]))
for language in languages:
    print(language)
    language_matrix = [[[] for _ in range(42)] for __ in range(11)]
    sub_df = term_df[term_df["name"] == language]
    sub_df = sub_df.drop_duplicates(subset=['consultant', 'CNUM'])
    #num_consultants = len(list(set(sub_df["consultant"])))
    terms = list(set(sub_df["TRAN"]))
    #for each color chip, count how often it got name with each color word
    term_sets = [{} for _ in range(331)]
    for i, row in sub_df.iterrows():
        trans = row["TRAN"]
        if trans != trans:
            continue
        if trans not in term_sets[row["CNUM"]]:
            term_sets[row["CNUM"]][trans] = 0
        term_sets[row["CNUM"]][trans] += 1

    #determine colors for each term by determining relevant color chips
    terms_colors = dict((term, []) for term in terms)
    for cnum, chip_terms in enumerate(term_sets):
        if cnum == 0:
            continue
        num_consultants = len(list(set(sub_df[sub_df["CNUM"] == cnum]["consultant"])))
        lightness, hue = code_to_coord[cnum]
        chip_terms = dict(sorted(chip_terms.items(), key=lambda item: item[1], reverse=True))
        if len(chip_terms) == 0:
            continue
        term = next(iter(chip_terms))
        #only take into account color chips for which sufficient consultants agree on this term
        if chip_terms[term] >= mix_threshold * num_consultants:
            term_color = matrix[lightness][hue]
            if len(term_color) == 0:
                continue
            terms_colors[term].append(term_color)
    #mix colors for each term
    mixed_colors = {}
    for term, colors in terms_colors.items():
        if len(colors) == 0:
            continue
        mixed_color = mix_colors(colors)
        mixed_colors[term] = mixed_color
        plt.scatter([], [], color = mixed_color, label = term)
    #color chips in respective colors
    for cnum, chip_terms in enumerate(term_sets):
        if cnum == 0:
            continue
        num_consultants = len(list(set(sub_df[sub_df["CNUM"] == cnum]["consultant"])))
        lightness, hue = code_to_coord[cnum]
        chip_terms = dict(sorted(chip_terms.items(), key=lambda item: item[1], reverse=True))
        if len(chip_terms) == 0:
            language_matrix[lightness][hue] = [1.0, 1.0, 1.0]
            continue
        colors_to_blend = []
        #fading and blending
        if fade:
            s = num_consultants
        else:
            s = 0
            i = 0
            for term, count in chip_terms.items():
                if term in mixed_colors:
                    s += count
                i += 1
                if i == num_blend:
                    break
        i = 0
        for term, count in chip_terms.items():
            if term in mixed_colors:
                colors_to_blend.append((mixed_colors[term], count / s))
            i += 1
            if i == num_blend:
                break
        final_color = blend_colors(colors_to_blend)
        language_matrix[lightness][hue] = final_color
    #draw using matplotlib
    fig,ax = plt.subplots(figsize=(40, 9))
    for lightness, r in enumerate(language_matrix):
        for hue, value in enumerate(r):
            if hue == 0 or len(value) == 0:
                continue
            rect = patches.Rectangle((0.025 * (hue - 1), 0.1 * lightness), 0.025, 0.1, linewidth=0, facecolor=value)
            ax.add_patch(rect)
    box = ax.get_position()
    #ax.set_position([box.x0, box.y0 + box.height * 0.1,
    #      box.width, box.height * 0.9])
    #ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.1),
    #          fancybox=True, shadow=True, ncol=11)
    ax.set_axis_off()

    plots_dir = os.path.join("plots")
    if not os.path.isdir(plots_dir):
        os.makedirs(plots_dir)
    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, language + "_" + str(mix_threshold).replace(".", "") + "_" + str(num_blend) + "_ " + str(int(fade)) + ".png"))
    plt.clf()
    plt.close()
