# Parts of this script were generated using generative AI (GPT-4o, GPT-4.1, GPT-5 mini through GitHub Copilot on Microsoft VS Code). All code, input data and results were manually reviewed ane edited. The author takes full responsibility for this work. The software is provided ``as is'' without any express or implied warranties.

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

data = [
    {"Project": "AcubeSAT", "Activity": "Training", "Days": 111},
    {"Project": "AcubeSAT", "Activity": "Design", "Days": 827},
    {"Project": "AcubeSAT", "Activity": "Procurement", "Days": 450},
    {"Project": "AcubeSAT", "Activity": "Software Development", "Days": 320},
    {"Project": "AcubeSAT", "Activity": "Manufacturing", "Days": 102},
    {"Project": "AcubeSAT", "Activity": "Assembly & Integration", "Days": 195},
    {"Project": "AcubeSAT", "Activity": "Structural Analysis", "Days": 234},
    {"Project": "AcubeSAT", "Activity": "Thermal Analysis", "Days": 124},
    {"Project": "AcubeSAT", "Activity": "Other Analysis", "Days": 228},
    {"Project": "AcubeSAT", "Activity": "Functional Testing", "Days": 346},
    {"Project": "AcubeSAT", "Activity": "Structural Testing", "Days": 79},
    {"Project": "AcubeSAT", "Activity": "Thermal Testing", "Days": 100},
    {"Project": "AcubeSAT", "Activity": "Other Environmental Testing", "Days": 121},
    
    {"Project": "PowerSat", "Activity": "Design", "Days": 40},
    {"Project": "PowerSat", "Activity": "Procurement", "Days": 43},
    {"Project": "PowerSat", "Activity": "Structural Analysis", "Days": 8},
    {"Project": "PowerSat", "Activity": "Thermal Analysis", "Days": 22},
    
    {"Project": "CLOVER-Sat", "Activity": "Feasibility Assessment", "Days": 60},
    {"Project": "CLOVER-Sat", "Activity": "Funding Search", "Days": 200},
    {"Project": "CLOVER-Sat", "Activity": "Design", "Days": 280},
    {"Project": "CLOVER-Sat", "Activity": "Manufacturing", "Days": 100},
    {"Project": "CLOVER-Sat", "Activity": "Functional Testing", "Days": 240},
    {"Project": "CLOVER-Sat", "Activity": "Structural Testing", "Days": 30},
    {"Project": "CLOVER-Sat", "Activity": "Thermal Testing", "Days": 30},
    
    {"Project": "Hermes", "Activity": "Training", "Days": 39},
    {"Project": "Hermes", "Activity": "Design", "Days": 300},
    {"Project": "Hermes", "Activity": "Review", "Days": 160},
    {"Project": "Hermes", "Activity": "Procurement", "Days": 80},
    {"Project": "Hermes", "Activity": "Manufacturing", "Days": 120},
    {"Project": "Hermes", "Activity": "Assembly & Integration", "Days": 180},
    {"Project": "Hermes", "Activity": "Functional Testing", "Days": 60},
    {"Project": "Hermes", "Activity": "Structural Testing", "Days": 45},
    {"Project": "Hermes", "Activity": "Thermal Testing", "Days": 45},
    
    {"Project": "NeAtO", "Activity": "Design", "Days": 122},
    {"Project": "NeAtO", "Activity": "Assembly & Integration", "Days": 25},
    {"Project": "NeAtO", "Activity": "Structural Analysis", "Days": 132},
    {"Project": "NeAtO", "Activity": "Thermal Analysis", "Days": 149},
    
    {"Project": "SPEISAT", "Activity": "Design", "Days": 60},
    {"Project": "SPEISAT", "Activity": "Procurement", "Days": 9},
    {"Project": "SPEISAT", "Activity": "Structural Analysis", "Days": 5},
    {"Project": "SPEISAT", "Activity": "Functional Testing", "Days": 21},
    {"Project": "SPEISAT", "Activity": "Structural Testing", "Days": 1},
]

df = pd.DataFrame(data)

activity_order = [
    "Feasibility Assessment", "Funding Search", "Training", "Design", "Review",
    "Procurement", "Software Development", "Manufacturing",
    "Assembly & Integration", "Structural Analysis", "Thermal Analysis",
    "Other Analysis", "Functional Testing", "Structural Testing",
    "Thermal Testing", "Other Environmental Testing"
]

df['Activity'] = pd.Categorical(df['Activity'], categories=activity_order, ordered=True)

sns.set_theme(style="whitegrid")
plt.figure(figsize=(12, 10))

counts = df.groupby('Activity')['Days'].count()
activities_with_multi_samples = counts[counts > 2].index.tolist()

sns.boxplot(
    data=df[df['Activity'].isin(activities_with_multi_samples)],
    x='Days', y='Activity',
    orient='h',
    color='lightgray',
    showfliers=False,
    boxprops=dict(alpha=0.3),
    whiskerprops=dict(alpha=0.3),
    capprops=dict(alpha=0.3),
    medianprops=dict(color='black', alpha=0.5)
)

unique_projects = df['Project'].unique()
palette = sns.color_palette("viridis", len(unique_projects))
project_colors = dict(zip(unique_projects, palette))

sns.scatterplot(
    data=df,
    x='Days', y='Activity',
    hue='Project',
    palette=palette,
    s=100,
    edgecolor='black',
    alpha=0.9,
    zorder=3
)

plt.xlabel("Time (days)", fontsize=12)
plt.ylabel("Activity Type", fontsize=12)
plt.legend(title="Project", bbox_to_anchor=(1, 0), loc='lower right')
plt.grid(True, linestyle='--', alpha=0.7)
plt.tight_layout()

plt.savefig('cubesat_durations_chart.pdf')
plt.show()