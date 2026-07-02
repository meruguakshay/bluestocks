#!/usr/bin/env python
"""
Simple Mutual Fund Recommender
Input: risk appetite (Low / Moderate / High)
Output: Top 3 funds by Sharpe ratio within matching risk_grade.
Prints a formatted recommendation table.
"""

import os
import sys
import pandas as pd

def recommend_funds(risk_appetite, scorecard_path="fund_scorecard.csv"):
    if not os.path.exists(scorecard_path):
        # Try to locate in the script directory if run from elsewhere
        script_dir = os.path.dirname(os.path.abspath(__file__))
        scorecard_path = os.path.join(script_dir, "fund_scorecard.csv")
        
    try:
        df = pd.read_csv(scorecard_path)
    except FileNotFoundError:
        print(f"Error: Could not locate 'fund_scorecard.csv'. Please make sure it is in the same directory as this script.")
        return None
        
    risk_appetite = risk_appetite.strip().lower()
    
    # Mapping risk appetite to risk_grade in scorecard
    if risk_appetite == 'low':
        grades = ['Low', 'Low to Moderate']
    elif risk_appetite == 'moderate':
        grades = ['Moderate', 'Moderate to High']
    elif risk_appetite == 'high':
        grades = ['High', 'Very High']
    else:
        print(f"Invalid risk appetite '{risk_appetite}'. Choose from: Low, Moderate, High.")
        return None
        
    # Filter
    filtered_df = df[df['risk_grade'].isin(grades)].copy()
    
    # Sort by Sharpe Ratio descending
    filtered_df = filtered_df.sort_values(by='sharpe_ratio', ascending=False)
    
    # Select top 3
    top_3 = filtered_df.head(3)
    
    # Select key columns
    cols = ['scheme_code', 'scheme_name', 'risk_grade', 'sharpe_ratio', 'cagr_3yr']
    top_3 = top_3[cols]
    
    return top_3

def main():
    print("=" * 80)
    print("                BLUESTOCK MUTUAL FUND RECOMMENDER SYSTEM")
    print("=" * 80)
    
    if len(sys.argv) > 1:
        appetite = sys.argv[1]
    else:
        appetite = input("Enter your risk appetite (Low / Moderate / High): ")
        
    res = recommend_funds(appetite)
    if res is not None:
        print(f"\nRecommended Funds for {appetite.upper()} Risk Appetite:")
        print("=" * 95)
        # Format table manually
        header = f"{'Scheme Code':<12} | {'Scheme Name':<45} | {'Risk Grade':<18} | {'Sharpe Ratio':<12} | {'3Yr Return (%)':<15}"
        print(header)
        print("-" * 95)
        for _, row in res.iterrows():
            cagr_3yr_val = row['cagr_3yr']
            # Convert return to percentage format if represented as a decimal fraction
            if abs(cagr_3yr_val) < 1.0:
                cagr_3yr_str = f"{cagr_3yr_val * 100:.2f}%"
            else:
                cagr_3yr_str = f"{cagr_3yr_val:.2f}%"
                
            line = f"{int(row['scheme_code']):<12} | {row['scheme_name'][:45]:<45} | {row['risk_grade']:<18} | {row['sharpe_ratio']:<12.4f} | {cagr_3yr_str:<15}"
            print(line)
        print("=" * 95)

if __name__ == "__main__":
    main()
