import streamlit as st
import yfinance as yf
import traceback
import requests

def obter_taxa_cambio():
    try:
        taxa = yf.Ticker("USDBRL=X").history(period="1d")["Close"].iloc[-1]
        return taxa
    except Exception as e:
        st.warning(f"Não foi possível buscar a cotação atual. [Confira](https://wise.com/br/currency-converter/usd-to-brl-rate) abaixo se a cotação padrão ainda é válida. ")
        print(f"Erro ao buscar a cotação: {e}")
        return 5.5  # :D

def obter_taxa_selic():
    url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados/ultimos/1?formato=json"
    
    try:
        response = requests.get(url)
        response.raise_for_status() 
        dados = response.json()
        
        if dados:
            return float(dados[0]["valor"])
    except Exception as e:
        print(f"Erro ao acessar a API: {e}")
    
    st.warning("Não foi possível acessar a API do Banco Central. [Confira](https://www.google.com/search?q=taxa+selic+atual) abaixo se a taxa padrão ainda é válida.")
    return 13.25  # :D

def calcular_rendimento_total(valor_investido, taxa_mensal, meses, parcela_mensal):
    saldo = valor_investido
    rendimento_total = 0

    for mes in range(1, meses + 1):
        if mes <= 6:
            ir = 0.225
        elif mes <= 12:
            ir = 0.20
        elif mes <= 24:
            ir = 0.175
        else:
            ir = 0.15

        # Calcula o rendimento bruto no mês
        rendimento_mes = saldo * taxa_mensal

        # Aplica o IR e atualiza o rendimento total
        rendimento_liquido = rendimento_mes * (1 - ir)
        rendimento_total += rendimento_liquido

        # Atualiza o saldo após retirar a parcela mensal
        saldo -= parcela_mensal

    return rendimento_total

def comparar_pagamentos(valor_vista, valor_parcelado, parcelas, taxa_mensal, cashback_percentual=0.0, pontos_por_dolar=0, valor_mil_pontos=30, taxa_cambio=5.0):
    try:
        # Cálculo do cashback
        cashback = valor_parcelado * cashback_percentual

        # Conversão do valor parcelado para dólares
        valor_parcelado_dolar = valor_parcelado / taxa_cambio

        # Cálculo dos pontos gerados (baseado em dólares)
        pontos = valor_parcelado_dolar * pontos_por_dolar
        valor_pontos = (pontos / 1000) * valor_mil_pontos

        # Cálculo do rendimento total ao pagar parcelado
        parcela_mensal = valor_parcelado / parcelas
        rendimento_total = calcular_rendimento_total(valor_parcelado, taxa_mensal, parcelas, parcela_mensal)

        # Valor máximo para valer a pena pagar à vista
        valor_maximo_a_vista = valor_parcelado - rendimento_total - cashback - valor_pontos

        # Desconto mínimo para valer a pena pagar à vista
        desconto_minimo = (rendimento_total + cashback + valor_pontos) / valor_parcelado * 100

        juros_str = f"Rendimento líquido acumulado: R$ {rendimento_total:.2f}"
        st.warning(juros_str)

        if cashback > 0 or valor_pontos > 0:
            if cashback > 0:
                st.warning(f"Cashback: R$ {cashback:.2f}")
            if valor_pontos > 0:
                st.warning(f"Pontos: R$ {valor_pontos:.2f} ({pontos:.0f} pontos)")

        st.info(f"Limite para pagamento à vista: R$ {valor_maximo_a_vista:.2f} (desconto mínimo aceitável: {desconto_minimo:.2f}%)")

        if valor_vista <= valor_maximo_a_vista:
            st.success("Conclusão: Pagar à vista.")
        else:
            st.success("Conclusão: Pagar parcelado.")

    except Exception as e:
        st.error("⚠️ Ocorreu um erro ao calcular os pagamentos. Verifique os valores informados e tente novamente.")
        print("Erro:", e)
        print(traceback.format_exc())

st.title("Pago à vista ou parcelado?")

# Criando colunas para os inputs
col1, col2 = st.columns(2)

with col1:
    valor_vista = st.number_input("Valor à vista (R$) – PIX, boleto ou em espécie:", min_value=0.0, value=100.0, step=1.0, format="%.2f")

with col2:
    valor_parcelado = st.number_input("Valor total parcelado (R$) - cartão de crédito:", min_value=0.0, value=100.0, step=1.0, format="%.2f")
    parcelas = st.number_input("Número de parcelas:", min_value=1, value=12, step=1, format="%d")

taxa_selic = obter_taxa_selic()
with st.expander("Alterar a taxa SELIC (%)"):
    taxa_anual = st.number_input("Taxa SELIC:", min_value=0.0, value=taxa_selic, step=0.01, format="%.2f") / 100

# Conversão da taxa anual para mensal
taxa_mensal = (1 + taxa_anual) ** (1 / 12) - 1

with col2:
    opcao = st.radio("Bonificação do cartão de crédito:", ("Cashback", "Pontos", "Nenhuma"))

    if opcao == "Cashback":
        cashback_percentual = st.number_input("Cashback (%):", min_value=0.0, value=0.5, step=0.1, format="%.1f") / 100
        pontos_por_dolar = 0  # Desativa pontos
        valor_mil_pontos = 0  # Desativa pontos
    elif opcao == "Pontos":
        pontos_por_dolar = st.number_input("Pontos por dólar gasto:", min_value=0.0, value=1.0, step=0.1, format="%.1f")
        valor_mil_pontos = st.number_input("Valor do milheiro (R$):", min_value=0.0, value=30.0, step=0.1, format="%.1f")
        st.info("Verifique o valor do seu milheiro com o banco que oferece o programa de pontos.")
        cashback_percentual = 0  # Desativa cashback
    else:
        # Caso o usuário não tenha bonificação
        cashback_percentual = 0  # Nenhum cashback
        pontos_por_dolar = 0  # Nenhum ponto
        valor_mil_pontos = 0  # Nenhum valor para pontos
        st.write("Você não tem bonificação no cartão de crédito.")

taxa_cambio = obter_taxa_cambio()
with st.expander("Alterar a cotação (USD) - dólar comercial"):
    taxa_cambio = st.number_input("Cotação:", min_value=0.0, value=taxa_cambio, step=0.01, format="%.2f")

if st.button("Calcular"):
    comparar_pagamentos(valor_vista, valor_parcelado, parcelas, taxa_mensal, cashback_percentual, pontos_por_dolar, valor_mil_pontos, taxa_cambio)

st.header("FAQ")
with st.expander("Como o valor rendeu ao longo do parcelamento?"):
    st.write("Ao parcelar, o valor que seria pago à vista permanece disponível e rende mensalmente com a taxa SELIC (a 100% CDI).")
    st.write("""
    A cada mês, o rendimento bruto é calculado e o Imposto de Renda (IR) é aplicado conforme o prazo de investimento:
    - Até 6 meses: 22,5%
    - De 6 a 12 meses: 20%
    - De 12 a 24 meses: 17,5%
    - Acima de 24 meses: 15%

    Os juros são aplicados ao saldo restante, que é atualizado mensalmente com o desconto da parcela do financiamento. O rendimento líquido é acumulado ao longo do período.
    """)

    st.write("Rendimento mensal:")
    st.latex(r"R_{\text{líquido}} = \text{Saldo} \times \text{Taxa mensal} \times (1 - IR)")

    st.write("""
    Onde:  
    - **Rendimento líquido**: Valor gerado após o desconto do imposto  
    - **Saldo**: Valor total disponível no início do mês  
    - **Taxa mensal**: Taxa de rendimento mensal correspondente  
    - **IR**: Percentual de Imposto de Renda aplicado conforme o período  
    """)

with st.expander("Como a taxa mensal foi calculada?"):
    st.write(f"Taxa mensal aproximada: {taxa_mensal * 100:.2f}%")
    st.write("A taxa mensal foi calculada a partir da taxa anual (SELIC) usando a seguinte fórmula:")
    st.latex(r"T_{\text{mensal}} = (1 + T_{\text{anual}})^{\frac{1}{12}} - 1")
    st.write("""
    Onde:
    - **Taxa anual**: A taxa SELIC fornecida pelo usuário.
    - **Taxa mensal**: A taxa mensal aproximada, usada no cálculo dos rendimentos.
    """)