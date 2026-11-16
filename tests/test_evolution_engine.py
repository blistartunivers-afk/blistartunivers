from motor.scripts.evolution import (
    create_random_genome,
    crossover_genomes,
    mutate_genome,
)


def test_seeded_genomes_are_reproducible_and_have_expected_shape():
    first = create_random_genome(seed=42)
    second = create_random_genome(seed=42)

    assert first == second
    assert first["architecture"] == [4, 8, 8, 1]
    assert len(first["w1"]) == len(first["w2"]) == 8
    assert all(len(row) == 4 for row in first["w1"])
    assert all(len(row) == 8 for row in first["w2"])
    assert len(first["w3"]) == 8


def test_mutation_advances_generation_without_changing_parent():
    parent = create_random_genome(seed=7)
    unchanged = create_random_genome(seed=7)
    child = mutate_genome(parent, mutation_rate=1.0, seed=19)

    assert parent == unchanged
    assert child["generation"] == 1
    assert child["w1"] != parent["w1"]
    assert all(-3 <= weight <= 3 for row in child["w1"] for weight in row)
    assert all(-3 <= weight <= 3 for row in child["w2"] for weight in row)
    assert all(-3 <= weight <= 3 for weight in child["w3"])


def test_crossover_uses_both_parents_without_changing_them():
    first = create_random_genome(seed=11)
    second = create_random_genome(seed=22)
    first_snapshot = create_random_genome(seed=11)
    second_snapshot = create_random_genome(seed=22)
    child = crossover_genomes(first, second, seed=33)

    assert first == first_snapshot
    assert second == second_snapshot
    assert child["generation"] == 1
    assert child["w1"] != first["w1"]
    assert child["w1"] != second["w1"]
    assert all(child["w1"][i] in (first["w1"][i], second["w1"][i]) for i in range(8))
