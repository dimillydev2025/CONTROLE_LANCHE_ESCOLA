CREATE DATABASE IF NOT EXISTS controle_lanche;
USE controle_lanche;

CREATE TABLE IF NOT EXISTS historico_lanches (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    id_aluno VARCHAR(100) NOT NULL,
    data_lanche DATE NOT NULL,
    UNIQUE KEY uq_historico_lanches_aluno_data (id_aluno, data_lanche)
);
