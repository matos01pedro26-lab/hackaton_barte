"""Domínio de checkout: comissão por lojista a partir das tabelas de data/ e das decisões em config/.

Camadas: leitura (tabelas e config) -> regras (taxa vigente, arredondamento) -> comissao (agregação,
rastro e pendências) -> saida (CSVs). Uso: python -m src.checkouts --mes 2026-09
"""
