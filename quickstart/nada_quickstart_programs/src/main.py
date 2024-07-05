from nada_dsl import *

def calculate_match_score(person1_attrs, person2_attrs, weights, max_age_difference):
    # Calculate age difference and match score
    person1_age = person1_attrs[0]
    person2_age = person2_attrs[0]
    age_diff = person1_age - person2_age
    age_diff = (person1_age > person2_age).if_else(age_diff, person2_age - person1_age)  # Ensures age_diff is positive
    age_match = max_age_difference - age_diff
    age_match = (age_match >= UnsignedInteger(0)).if_else(weights[0], UnsignedInteger(0))

    # Calculate interest match
    interested_in_match1 = person1_attrs[2] == person2_attrs[1]
    interested_in_match2 = person2_attrs[2] == person1_attrs[1]
    interest_match_int1 = interested_in_match1.if_else(UnsignedInteger(1), UnsignedInteger(0))
    interest_match_int2 = interested_in_match2.if_else(UnsignedInteger(1), UnsignedInteger(0))
    interested_in_match = interest_match_int1 * interest_match_int2 * weights[2]

    # Combine age and interest matches
    match_score = age_match + interested_in_match

    # Calculate attribute matches
    for i in range(3, len(person1_attrs)):
        person1_attr = person1_attrs[i]
        person2_attr = person2_attrs[i]
        attribute_diff = person1_attr - person2_attr
        attribute_diff = (person1_attr > person2_attr).if_else(attribute_diff, person2_attr - person1_attr)
        attribute_match = weights[i] - attribute_diff
        match_score = match_score + attribute_match

    return match_score

def secure_matching(nr_people, people_attributes, weights, max_age_difference, outparty):
    match_results = []

    for p1 in range(nr_people):
        for p2 in range(p1 + 1, nr_people):
            match_score = calculate_match_score(people_attributes[p1], people_attributes[p2], weights, max_age_difference)
            match_results.append(Output(match_score, f"match_score_p{p1}_p{p2}", outparty))

    return match_results

def initialize_parties(nr_parties, prefix):
    parties = []
    for i in range(nr_parties):
        parties.append(Party(name=f"{prefix}{i}"))
    return parties

def inputs_initialization(nr_people, attributes, parties):
    people_attributes = []

    for p in range(nr_people):
        attributes_list = []
        for attr in attributes:
            attributes_list.append(SecretUnsignedInteger(Input(name=f"p{p}_{attr}", party=parties[p])))
        people_attributes.append(attributes_list)

    return people_attributes

def nada_main():
    nr_people = 3
    attributes = ["age", "gender", "interested_in", "honesty", "humor", "adventure", "music", "cooking"]
    weights = [UnsignedInteger(10), UnsignedInteger(0), UnsignedInteger(30), UnsignedInteger(20), UnsignedInteger(25), UnsignedInteger(15), UnsignedInteger(20), UnsignedInteger(10)]
    max_age_difference = UnsignedInteger(5)

    people = initialize_parties(nr_people, "Person")
    outparty = Party(name="OutParty")

    people_attributes = inputs_initialization(nr_people, attributes, people)
    match_results = secure_matching(nr_people, people_attributes, weights, max_age_difference, outparty)

    return match_results

# Compile and run the main program
if __name__ == "__main__":
    nada_main()
