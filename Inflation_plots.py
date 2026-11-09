import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import pandas as pd

# Data
pay_classes = ["APS2", "APS3", "APS4", "APS5", "APS6", "EL1", "EL2 L", "EL2 U"]


def read_pay_csv(path):
    """Read a Fortnightly Pay CSV exported from LibreOffice."""
    df = pd.read_csv(path, index_col="Pay Date")
    df.index = pd.to_datetime(df.index, dayfirst=True)  # dates are d/mm/yyyy
    # if exported "as shown", pay looks like " $2,209 " - strip $ , and spaces
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = pd.to_numeric(df[col].str.replace(r"[$,\s]", "", regex=True))
    return df


df = read_pay_csv("Fortnightly Pay - APSC.csv")     # actual pay + CPI/SLCI
cpsu = read_pay_csv("Fortnightly Pay - CPSU.csv")   # CPSU scenario pay


index_dict = {'SLCI': 'Fortnightly SLCI', 'CPI': 'Fortnightly CPI'}


for pay_level in pay_classes:
    col = f"{pay_level} Fortnightly Pay"
    print(col, col in df.columns)

# Process CPI and SLCI
for inflation_index in index_dict:
    print("processing",inflation_index)

    # process each pay class
    for pay_level in pay_classes:

        # Starting value
        start_value = df[f"{pay_level} Fortnightly Pay"].iloc[0]

        # the values to multiply pay by (1.XXXX)
        multiplier = 1 + df[index_dict[inflation_index]] / 100

        # Calculate compounded column
        df[f"{pay_level} Fortnightly Pay with " + inflation_index] = start_value * multiplier.cumprod()

        # difference between inflation adjusted and actual pay
        df[f"{pay_level} Difference"] = (
            df[f"{pay_level} Fortnightly Pay with " + inflation_index] - df[f"{pay_level} Fortnightly Pay"]
        )

        #cumulative difference
        df[f"{pay_level} cumulative difference"] = df[f"{pay_level} Difference"].cumsum()
    print("Pay classes:", pay_classes)
    print("pay classes:", len(pay_classes))

    # Plot
    fig, axes = plt.subplots(4, 2, figsize=(14,13), layout='constrained')
    print("axes:", len(axes.ravel()))
    xmin = df.index.min()
    xmax = df.index.max()

    for a in axes.ravel():
        a.set_xlim(xmin, xmax)

    cutoff = pd.Timestamp("2026-03-12")

    for pay_level, ax in zip(pay_classes, axes.ravel()):
        print("plotting", pay_level)

        def plot_series(series, label, color, linestyle="-", dotted_projection=True):
            if not dotted_projection:
                ax.plot(series.index, series.values, color=color, linewidth=2,
                        linestyle=linestyle, label=label)
                return
            before = series[series.index <= cutoff]
            after = series[series.index > cutoff]

            if not before.empty:
                ax.plot(before.index, before.values, color=color, linewidth=2,
                        linestyle=linestyle, label=label)
            if not after.empty:
                ax.plot(after.index, after.values, color=color, linewidth=2,
                        linestyle=":", label="_nolegend_")

        plot_series(
            df[f"{pay_level} Fortnightly Pay with " + inflation_index],
            f"Inflation adjusted ({inflation_index})",
            color="tab:blue",
        )
        plot_series(
            df[f"{pay_level} Fortnightly Pay"],
            "APSC offer of 3.2%, 3.0%, 2.8% per year",
            color="tab:green",
            dotted_projection=False,
        )

        # CPSU line: only drawn from the pay date before it splits off from APSC
        cpsu_pay = cpsu[f"{pay_level} Fortnightly Pay"].copy()
        differs = (cpsu_pay != df[f"{pay_level} Fortnightly Pay"]).to_numpy()
        if differs.any():
            cpsu_pay.iloc[:max(differs.argmax() - 1, 0)] = float("nan")
        plot_series(cpsu_pay, "CPSU claim of 5%, 5%, 5% per year", color="tab:red",
                    dotted_projection=False)

        years = pd.date_range(xmin, xmax, freq='YS')
        ax.set_xticks(years)
        ax.set_xticklabels([y.year for y in years])
        ax.set_xlabel('Year')

        ax.yaxis.set_major_formatter(mtick.StrMethodFormatter('${x:,.0f}'))
        ax.set_ylabel('Gross Fortnightly Pay ($)')
        ax.grid(alpha=0.5)
        ax.set_title(pay_level, fontsize=14)

        ax.plot([], [], color='k', linestyle=':', linewidth=2,
                label='projected inflation (RBA Outlook 11/2026)')
        ax.legend(loc='upper left', frameon=False, fontsize=10)

        ax.text(
                .02, .45,
                'APSC Total Cumulative Difference=${:,.0f}'.format(
                    df[f"{pay_level} cumulative difference"].iloc[-1]
                ),
                transform=ax.transAxes, fontsize=11
            )

        cpsu_cum = (df[f"{pay_level} Fortnightly Pay with " + inflation_index]
                    - cpsu[f"{pay_level} Fortnightly Pay"]).sum()
        ax.text(.02, .38, f'CPSU Total Cumulative Difference=${cpsu_cum:,.0f}',
                transform=ax.transAxes, fontsize=11)

    # fig.delaxes(axes[3, 1])
    fig.savefig('inflation_adjusted_pay_comparison_' + inflation_index + '.png', bbox_inches='tight', dpi=300)

