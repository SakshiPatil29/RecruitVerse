def compare_candidates(

        candidate_a,

        candidate_b):


    if candidate_a["score"] > candidate_b["score"]:


        better = candidate_a["name"]


    else:


        better = candidate_b["name"]


    return {

        "candidate_a_score":

            candidate_a["score"],


        "candidate_b_score":

            candidate_b["score"],


        "better_candidate":

            better,


        "reason":

            "Higher skill match"

    }