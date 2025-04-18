USE crimewarehouse;

WITH robos_por_dia AS (
SELECT 
	fct.FECHA,
	COUNT(fct.CONTACTO_ID) AS cantidad_robos
FROM
	FCT_HECHOS fct
INNER JOIN
	DIM_TIPO_DELITO dtd
ON fct.TIPO_DELITO_KEY = dtd.TIPO_DELITO_KEY
WHERE
	dtd.TIPO_DELITO_DESC = 'Robo'
GROUP BY FECHA
)

SELECT
	AVG(cantidad_robos)
FROM
	robos_por_dia
	
