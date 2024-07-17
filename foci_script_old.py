import os
import pandas as pd
import string
from colorspacious import cspace_converter
import matplotlib.pyplot as plt
import matplotlib.patches as patches





##################################### OLD SCRIPT USING FOCI DATA DOES NOT CREATE NICE PLOTS #######################################





def mix_colors(colors):
    concentration = 1.0 / len(colors)
    color = [v * concentration for v in colors[0]]
    for next_color in colors[1:]:
        for i, v in enumerate(next_color):
            color[i] += concentration * v
    return color


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

foci_df = pd.read_csv("foci_exp.txt", sep = "\t")
lang_df = pd.read_csv("lang.txt", sep = "\t")
dict_df = pd.read_csv("dict.txt", sep = "\t")
foci_df = pd.merge(foci_df, lang_df, how = 'left', left_on="#LNUM", right_on = "#LNUM")
foci_df = pd.merge(foci_df, dict_df, how = 'left', left_on=["#LNUM", "TNUM"], right_on = ["#LNUM", "TNUM"])

languages = list(set(foci_df["name"]))
for language in languages:
    fig,ax = plt.subplots(figsize=(21, 5))
    language_matrix = [[[] for _ in range(42)] for __ in range(11)]
    sub_df = foci_df[foci_df["name"] == language]
    terms = list(set(sub_df["TRAN"]))
    for term in terms:
        sub_sub_df = sub_df[sub_df["TRAN"] == term]
        coordinate_strings = list(sub_sub_df["chip"])
        coordinates = []
        term_colors = []
        for coordinate_string in coordinate_strings:
            lightness = string.ascii_uppercase.index(coordinate_string[0])
            hue = int(coordinate_string[1:])
            term_color = matrix[lightness][hue]
            if len(term_color) == 0:
                print(str(lightness), str(hue))
                continue
            term_colors.append(term_color)
            coordinates.append((lightness, hue))
        if len(term_colors) == 0:
            continue
        mixed_color = mix_colors(term_colors)
        plt.scatter([], [], color = mixed_color, label = term)
        for lightness, hue in coordinates:
            language_matrix[lightness][hue] = mixed_color
    for lightness, r in enumerate(language_matrix):
        for hue, value in enumerate(r):
            if len(value) == 0:
                continue
            rect = patches.Rectangle((0.025 * hue, 0.1 * lightness), 0.025, 0.1, linewidth=0, facecolor=value)
            ax.add_patch(rect)
    box = ax.get_position()
    ax.set_position([box.x0, box.y0 + box.height * 0.1,
          box.width, box.height * 0.9])
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.1),
              fancybox=True, shadow=True, ncol=11)
    ax.set_axis_off()
    plt.savefig("foci_plots/" + language + ".png")
    plt.clf()
    plt.close()
    #break
