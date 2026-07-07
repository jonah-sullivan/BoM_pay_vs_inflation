
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import matplotlib.dates as mdates

# Data
pay_classes = ["APS3", "APS4", "APS5", "APS6", "EL1", "EL2 L", "EL2 U"]

df = pd.read_excel("fortnightly_pay.xlsx",
        sheet_name="Fortnightly Pay",
        parse_dates=["Pay Date"],
        index_col="Pay Date")

df.index = pd.to_datetime(df.index)
index_dict = {'SLCI': 'Fortnightly SLCI', 'CPI': 'Fortnightly CPI'}


for pay_level in pay_classes:
    col = f"{pay_level} Fortnightly Pay"
    print(col, col in df.columns)

# Process CPI and SLCI
for inflation_index in index_dict.keys():
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

    for pay_level, ax in zip(pay_classes, axes.ravel()):
        print("plotting", pay_level)
        df[f"{pay_level} Fortnightly Pay with " + inflation_index].plot(
            ax=ax, label=f"Inflation adjusted ({inflation_index})"
        )
        df[f"{pay_level} Fortnightly Pay"].plot(
            ax=ax, label="Actual pay"
        )

        years = pd.date_range(xmin, xmax, freq='YS')
        ax.set_xticks(years)
        ax.set_xticklabels([y.year for y in years])
        ax.set_xlabel('Year')

        ax.yaxis.set_major_formatter(mtick.StrMethodFormatter('${x:,.0f}'))
        ax.set_ylabel('Gross Fortnightly Pay ($)')
        ax.grid(alpha=0.5)
        ax.set_title(pay_level, fontsize=14)

        ax.legend(loc='upper left', frameon=False, fontsize=10)

        
        ax.text(
                .02, .65,
                'Total Cumulative Difference=${:,.0f}'.format(
                    df[f"{pay_level} cumulative difference"].iloc[-1]
                ),
                transform=ax.transAxes, fontsize=11
            )

    fig.delaxes(axes[3, 1])
    fig.savefig(f'inflation_adjusted_pay_comparison_' + inflation_index + '.png', bbox_inches='tight', dpi=300)




