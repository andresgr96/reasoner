import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os
from scipy.stats import mannwhitneyu

results_file = "./results/reasoning_results.csv"
df = pd.read_csv(results_file)

def normalize_metrics(data):
    """Normalize runtime and subsumers found per reasoner."""
    normalized_data = data.copy()
    for metric in ["Runtime (s)", "Subsumers Found"]:
        min_val = data[metric].min()
        max_val = data[metric].max()
        normalized_data[metric] = (data[metric] - min_val) / (max_val - min_val)
    return normalized_data

def plot_normalized_distributions(data, output_folder="./results/plots"):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    normalized_data = normalize_metrics(data)

    # Plot normalized runtime distribution
    plt.figure(figsize=(10, 6))
    sns.violinplot(x="Reasoner", y="Runtime (s)", data=normalized_data)
    plt.title("Normalized Runtime Distribution Across All Ontologies")
    plt.ylabel("Normalized Runtime (s)")
    plt.savefig(f"{output_folder}/normalized_runtime_violin.png")
    plt.close()

    # Plot normalized subsumers found distribution
    plt.figure(figsize=(10, 6))
    sns.violinplot(x="Reasoner", y="Subsumers Found", data=normalized_data)
    plt.title("Normalized Subsumers Found Distribution Across All Ontologies")
    plt.ylabel("Normalized Subsumers Found")
    plt.savefig(f"{output_folder}/normalized_subsumers_violin.png")
    plt.close()

    # Plot runtime distribution as a boxplot
    plt.figure(figsize=(10, 6))
    sns.boxplot(x="Reasoner", y="Runtime (s)", data=data)
    plt.title("Runtime Distribution Across All Ontologies (Boxplot)")
    plt.ylabel("Runtime (s)")
    plt.savefig(f"{output_folder}/runtime_boxplot.png")
    plt.close()

# Statistical tests
def statistical_tests(data):
    aggregated = data.groupby("Reasoner").agg({
        "Runtime (s)": list,
        "Subsumers Found": list
    }).to_dict(orient="index")

    # Custom vs. Elk and Custom vs. Hermit 
    results = []
    for metric in ["Runtime (s)", "Subsumers Found"]:
        custom_values = aggregated["custom"][metric]
        elk_values = aggregated["elk"][metric]
        hermit_values = aggregated["hermit"][metric]

        # Mann-Whitney U test
        stat_custom_vs_elk, p_custom_vs_elk = mannwhitneyu(custom_values, elk_values, alternative='two-sided')
        stat_custom_vs_hermit, p_custom_vs_hermit = mannwhitneyu(custom_values, hermit_values, alternative='two-sided')

        results.append({
            "Metric": metric,
            "Comparison": "Custom vs. Elk",
            "Statistic": stat_custom_vs_elk,
            "p-value": p_custom_vs_elk
        })
        results.append({
            "Metric": metric,
            "Comparison": "Custom vs. Hermit",
            "Statistic": stat_custom_vs_hermit,
            "p-value": p_custom_vs_hermit
        })

    results_df = pd.DataFrame(results)
    results_df.to_csv("./results/statistical_tests.csv", index=False)
    print("Statistical tests saved to ./results/statistical_tests.csv")

if __name__ == "__main__":
    normalized_df = normalize_metrics(df)
    plot_normalized_distributions(df)
    
    statistical_tests(df)
