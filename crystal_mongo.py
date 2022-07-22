import glob
import pandas as pd
import numpy as np
import json
import pickle
from bson.binary import Binary
from pymongo import MongoClient
import certifi
from ast import literal_eval

from pymatgen.core import Lattice, Structure
from crystal_out import crystalOut

def crystal_mongo_drone():
    all_crystal_outputs = glob.glob("../project_Raman/crystal17_output_files/*/*.out")
    print("Found", len(all_crystal_outputs), "structures to be loaded into mongodb...")

    print("Structures identified to have errors:")
    print("popped:", all_crystal_outputs.pop(52))
    print("popped:", all_crystal_outputs.pop(52))

    mc = MongoClient("orion.nus.edu.sg", 27017)
    db = mc["raman_ml"]
    structures = db.structures

    for s in all_crystal_outputs:
        selected_structure = crystalOut(s)
        name = s.split("\\")[-1]
        print("Doing", name)
        bornChargeArrayList = []
        for val in selected_structure.bornCharge.values():
            bornChargeArrayList.append(val["Born Charge"])
        bornChargeArray = np.concatenate(bornChargeArrayList, dtype = "float64")

        structure = {"structure_name": name,
                    "structure":json.dumps(selected_structure.structure.as_dict()), 
                    "spaceGroup":selected_structure.parsed_data["space_group"],
                    "thermodynamicTerms":json.dumps(selected_structure.thermodynamicTerms),
                    "dielectricTensor":Binary(pickle.dumps(selected_structure.dielectricTensor, protocol=2), subtype=128),
                    "vibContributionsDielectric":Binary(pickle.dumps(selected_structure.vibContributionsDielectric, protocol=2), subtype=128),
                    "secondElectricSusceptibility":Binary(pickle.dumps(selected_structure.secondElectricSusceptibility, protocol=2), subtype=128),
                    "thirdElectricSusceptibility":Binary(pickle.dumps(selected_structure.thirdElectricSusceptibility, protocol=2), subtype=128),
                    "bornChargeArray":Binary(pickle.dumps(bornChargeArray, protocol=2), subtype=128),
                    "bornChargeNormalModeBasis":Binary(pickle.dumps(selected_structure.bornChargeNormalModeBasis, protocol=2), subtype=128),
                    "intRaman":json.dumps(selected_structure.intRaman)}

        structure_id = structures.insert_one(structure).inserted_id
        print("Done", structure_id)

def load_structure_from_mongo(structure_name):
    client = MongoClient("mongodb+srv://pengfei:rWAhoVdf25suZeqh@cluster0.1wcvyoq.mongodb.net/?retryWrites=true&w=majority", tlsCAFile=certifi.where())
    db = client['test']
    structures = db.structures
    structure_name_out = structure_name + ".out"
    query = structures.find_one({"structure_name":structure_name_out})

    structure = Structure.from_dict(json.loads(query["structure"]))
    spaceGroup = query["spaceGroup"]
    thermodynamicTerms = json.loads(query["thermodynamicTerms"])
    intRaman = json.loads(query["intRaman"])

    dielectricTensor = pickle.loads(query["dielectricTensor"])
    vibContributionsDielectric = pickle.loads(query["vibContributionsDielectric"])
    secondElectricSusceptibility = pickle.loads(query["secondElectricSusceptibility"])
    thirdElectricSusceptibility = pickle.loads(query["thirdElectricSusceptibility"])
    bornChargeArray = pickle.loads(query["bornChargeArray"])
    bornChargeNormalModeBasis = pickle.loads(query["bornChargeNormalModeBasis"])

    return structure, spaceGroup, thermodynamicTerms, intRaman, dielectricTensor, vibContributionsDielectric, secondElectricSusceptibility, thirdElectricSusceptibility, bornChargeArray, bornChargeNormalModeBasis


if __name__ == '__main__':
    crystal_mongo_drone()