import streamlit as st
import yfinance as yf

def obter_taxa_cambio():
    # Busca a taxa de câmbio do dólar (USD para BRL)
    try:
        taxa = yf.Ticker("USDBRL=X").history(period="1d")["Close"].iloc[-1]
        return taxa
    except Exception as e:
        st.warning(f"Não foi possível buscar a taxa de câmbio. Erro: {e}")
        return 5.0  # Valor padrão em caso de erro

def calcular_rendimento_total(valor_investido, taxa_mensal, meses, parcela_mensal):
    saldo = valor_investido
    rendimento_total = 0  # Acumula o rendimento bruto

    for mes in range(1, meses + 1):
        # Aplica a taxa de IR conforme o período
        if mes <= 6:
            ir = 0.225  # 22,5%
        elif mes <= 12:
            ir = 0.20  # 20%
        elif mes <= 24:
            ir = 0.175  # 17,5%
        else:
            ir = 0.15  # 15%

        # Calcula o rendimento bruto no mês
        rendimento_mes = saldo * taxa_mensal

        # Aplica o IR sobre o rendimento
        rendimento_liquido = rendimento_mes * (1 - ir)

        # Adiciona o rendimento líquido ao total
        rendimento_total += rendimento_liquido

        # Atualiza o saldo após retirar a parcela mensal
        saldo -= parcela_mensal

    return rendimento_total

def comparar_pagamentos(valor_vista, valor_parcelado, parcelas, taxa_mensal, cashback_percentual=0.00, pontos_por_dolar=0, valor_mil_pontos=30, taxa_cambio=5.0):
    # Cálculo do cashback
    cashback = valor_parcelado * cashback_percentual

    # Conversão do valor parcelado para dólares
    valor_parcelado_dolar = valor_parcelado / taxa_cambio

    # Cálculo dos pontos gerados (baseado em dólares)
    pontos = valor_parcelado_dolar * pontos_por_dolar
    valor_pontos = (pontos / 1000) * valor_mil_pontos

    # Cálculo do rendimento total ao pagar parcelado
    parcela_mensal = valor_parcelado / parcelas  # Valor da parcela mensal
    rendimento_total = calcular_rendimento_total(valor_parcelado, taxa_mensal, parcelas, parcela_mensal)

    # Valor máximo que compensa pagar à vista (valor financiado - juros - cashback - valor dos pontos)
    valor_maximo_a_vista = valor_parcelado - rendimento_total - cashback - valor_pontos

    # Desconto mínimo para valer a pena pagar à vista
    desconto_minimo = (rendimento_total + cashback + valor_pontos) / valor_parcelado * 100

    # Exibição dos resultados
    juros_str = f"Juros gerados ao pagar parcelado: R$ {rendimento_total:.2f}"
    st.write(juros_str)
    # Exemplo da lógica de rendimento (em um expander)
    with st.expander("Como o valor rendeu ao longo do parcelamento?"):
        st.write("""
        O valor investido rende mensalmente com base na taxa mensal fornecida.
        A cada mês, o rendimento bruto é calculado e o Imposto de Renda (IR) é aplicado conforme o período:
        - Até 6 meses: 22,5%
        - De 6 a 12 meses: 20%
        - De 12 a 24 meses: 17,5%
        - Acima de 24 meses: 15%

        O saldo é atualizado a cada mês com o débito da parcela do parcelamento, e o rendimento líquido é acumulado.
        """)
    if cashback > 0 or valor_pontos > 0:
        if cashback > 0:
            cashback_str = f"Cashback: R$ {cashback:.2f}"
            st.write(cashback_str)
        if valor_pontos > 0:
            pontos_str = f"Pontos: R$ {valor_pontos:.2f}"
            st.write(pontos_str)

    st.write(f"Valor máximo para pagar à vista: R$ {valor_maximo_a_vista:.2f} (com desconto mínimo de: {desconto_minimo:.2f}%)")

    if valor_vista <= valor_maximo_a_vista:
        st.success("Conclusão: Pagar à vista.")
        total_economizado = valor_maximo_a_vista - valor_vista
        st.write(f"Total economizado ao pagar à vista: R$ {total_economizado:.2f}")
    else:
        st.success("Conclusão: Pagar parcelado.")
        total_economizado = valor_parcelado - valor_maximo_a_vista
        st.write(f"Total economizado ao pagar parcelado: R$ {total_economizado:.2f}")

    st.write(f"Taxa mensal considerada: {taxa_mensal * 100:.2f}%")

st.title("Simulador de Pagamento à Vista vs. Parcelado")

# Inputs do usuário
valor_vista = st.number_input("Valor à vista (R$):", min_value=0.0, value=3300.0, step=0.01, format="%.2f")
valor_parcelado = st.number_input("Valor total parcelado (R$):", min_value=0.0, value=3700.0, step=0.01, format="%.2f")
parcelas = st.number_input("Número de parcelas:", min_value=1, value=12, step=1, format="%d")

# Taxa anual (SELIC)
taxa_anual = st.number_input("Taxa SELIC (%):", min_value=0.0, value=13.25, step=0.01, format="%.2f") / 100

# Conversão da taxa anual para mensal
taxa_mensal = (1 + taxa_anual) ** (1 / 12) - 1

# Seleção entre cashback ou pontos
opcao = st.radio("Escolha o tipo de benefício:", ("Cashback", "Pontos"))

if opcao == "Cashback":
    cashback_percentual = st.number_input("Cashback (%):", min_value=0.0, value=1.0, step=0.01, format="%.2f") / 100
    pontos_por_dolar = 0  # Desativa pontos
    valor_mil_pontos = 0  # Desativa pontos
else:
    pontos_por_dolar = st.number_input("Pontos por dólar gasto:", min_value=0.0, value=0.0, step=0.01, format="%.2f")
    valor_mil_pontos = st.number_input("Valor de 1000 pontos (R$):", min_value=0.0, value=30.0, step=0.01, format="%.2f")
    cashback_percentual = 0  # Desativa cashback

# Taxa de câmbio
taxa_cambio = obter_taxa_cambio()
with st.expander("Alterar taxa de câmbio (dólar)"):
    taxa_cambio = st.number_input("Taxa de câmbio:", min_value=0.0, value=taxa_cambio, step=0.01, format="%.2f")

# Botão para calcular
if st.button("Calcular"):
    comparar_pagamentos(valor_vista, valor_parcelado, parcelas, taxa_mensal, cashback_percentual, pontos_por_dolar, valor_mil_pontos, taxa_cambio)