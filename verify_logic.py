import search_engine
import business_logic
import cnae_mapping
import pandas as pd

def test_flow():
    print("Testing Radar Ambiental Logic...")
    
    # Simulate user selecting group "06.00"
    grupo_id = "06.00"
    print(f"Selected Group: {grupo_id} - {cnae_mapping.LEI_TO_CNAE[grupo_id]['descricao']}")
    
    cnaes_do_grupo = cnae_mapping.LEI_TO_CNAE[grupo_id]['cnaes']
    print(f"Target CNAE count: {len(cnaes_do_grupo)}")
    
    # 1. Search
    print("Executing Search (Mock Mode)...")
    results = search_engine.buscar_empresas(cnae_alvo=cnaes_do_grupo, mock_mode=True)
    print(f"Found {len(results)} raw results.")
    
    # 2. Logic
    print("Applying Business Logic...")
    processed = business_logic.analisar_leads(results, grupo_id, cnaes_do_grupo)
    print(f"Processed {len(processed)} qualified leads.")
    
    if processed:
        df = pd.DataFrame(processed)
        print("\nSample Data:")
        print(df[['razao_social', 'cnae_fiscal_principal', 'status_radar']].head())
        
        initial = len(df[df['status_radar'].str.contains("Inicial")])
        rama = len(df[df['status_radar'].str.contains("RAMA")])
        print(f"\nStats: Initial: {initial}, RAMA: {rama}")
        
    print("\nTesting Risk Tag Logic (Group 03.00)...")
    grupo_risk = "03.00"
    cnaes_risk = cnae_mapping.LEI_TO_CNAE[grupo_risk]['cnaes']
    results_risk = search_engine.buscar_empresas(cnae_alvo=cnaes_risk, mock_mode=True)
    processed_risk = business_logic.analisar_leads(results_risk, grupo_risk, cnaes_risk)
    
    risk_count = 0
    if processed_risk:
         for p in processed_risk:
             if p['tag_risco'] == "ALTO POTENCIAL":
                 risk_count += 1
    print(f"Items with Risk Tag in Group 03.00: {risk_count}/{len(processed_risk)}")

if __name__ == "__main__":
    test_flow()
