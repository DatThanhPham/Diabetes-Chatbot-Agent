# Logic được suy ra từ file clean_2023.ipynb của bạn

def validate_health_form(data):
    """
    Xác thực 19 trường dữ liệu từ form.
    Nếu hợp lệ, trả về (True, data).
    Nếu không hợp lệ, trả về (False, error_message).
    """
    try:
        # 1. HighBP (High Blood Pressure)
        # _RFHYPE6: 1:0, 2:1. Yêu cầu frontend gửi 0 hoặc 1
        high_bp = float(data['HighBP'])
        if high_bp not in [0.0, 1.0]: raise ValueError("HighBP")

        # 2. HighChol (High Cholesterol)
        # TOLDHI3: 2:0, 1:1. Yêu cầu frontend gửi 0 hoặc 1
        high_chol = float(data['HighChol'])
        if high_chol not in [0.0, 1.0]: raise ValueError("HighChol")

        # 3. CholCheck (Cholesterol Check)
        # _CHOLCH3: 3:0, 2:0, 1:1. Yêu cầu frontend gửi 0 hoặc 1
        chol_check = float(data['CholCheck'])
        if chol_check not in [0.0, 1.0]: raise ValueError("CholCheck")

        # 4. BMI
        # _BMI5: div(100).round(0). Frontend gửi số thực
        bmi = float(data['BMI'])
        if not (12.0 <= bmi <= 99.0): raise ValueError("BMI")

        # 5. Smoker
        # SMOKE100: 2:0, 1:1. Yêu cầu frontend gửi 0 hoặc 1
        smoker = float(data['Smoker'])
        if smoker not in [0.0, 1.0]: raise ValueError("Smoker")

        # 6. Stroke
        # CVDSTRK3: 2:0, 1:1. Yêu cầu frontend gửi 0 hoặc 1
        stroke = float(data['Stroke'])
        if stroke not in [0.0, 1.0]: raise ValueError("Stroke")

        # 7. HeartDiseaseorAttack
        # _MICHD: 2:0, 1:1. Yêu cầu frontend gửi 0 hoặc 1
        heart_disease = float(data['HeartDiseaseorAttack'])
        if heart_disease not in [0.0, 1.0]: raise ValueError("HeartDiseaseorAttack")

        # 8. PhysActivity
        # _TOTINDA: 2:0, 1:1. Yêu cầu frontend gửi 0 hoặc 1
        phys_activity = float(data['PhysActivity'])
        if phys_activity not in [0.0, 1.0]: raise ValueError("PhysActivity")

        # 9. HvyAlcoholConsump (Heavy Alcohol Consumption)
        # _RFDRHV8: 1:0, 2:1. Yêu cầu frontend gửi 0 hoặc 1
        hvy_alcohol = float(data['HvyAlcoholConsump'])
        if hvy_alcohol not in [0.0, 1.0]: raise ValueError("HvyAlcoholConsump")

        # 10. AnyHealthcare
        # _HLTHPL1: 2:0, 1:1. Yêu cầu frontend gửi 0 hoặc 1
        any_healthcare = float(data['AnyHealthcare'])
        if any_healthcare not in [0.0, 1.0]: raise ValueError("AnyHealthcare")

        # 11. NoDocbcCost (No Doctor because of Cost)
        # MEDCOST1: 2:0, 1:1. Yêu cầu frontend gửi 0 hoặc 1
        no_doc_cost = float(data['NoDocbcCost'])
        if no_doc_cost not in [0.0, 1.0]: raise ValueError("NoDocbcCost")

        # 12. GenHlth (General Health)
        # GENHLTH: 1-5.
        gen_hlth = float(data['GenHlth'])
        if gen_hlth not in [1.0, 2.0, 3.0, 4.0, 5.0]: raise ValueError("GenHlth")

        # 13. MentHlth (Mental Health)
        # MENTHLTH: 88:0. 0-30.
        ment_hlth = float(data['MentHlth'])
        if not (0.0 <= ment_hlth <= 30.0): raise ValueError("MentHlth")

        # 14. PhysHlth (Physical Health)
        # PHYSHLTH: 88:0. 0-30.
        phys_hlth = float(data['PhysHlth'])
        if not (0.0 <= phys_hlth <= 30.0): raise ValueError("PhysHlth")

        # 15. DiffWalk (Difficulty Walking)
        # DIFFWALK: 2:0, 1:1. Yêu cầu frontend gửi 0 hoặc 1
        diff_walk = float(data['DiffWalk'])
        if diff_walk not in [0.0, 1.0]: raise ValueError("DiffWalk")

        # 16. Sex
        # SEXVAR: 2:0, 1:1. Yêu cầu frontend gửi 0 (Nữ) hoặc 1 (Nam)
        sex = float(data['Sex'])
        if sex not in [0.0, 1.0]: raise ValueError("Sex")

        # 17. Age
        # _AGEG5YR: 1-13.
        age = float(data['Age'])
        if not (1.0 <= age <= 13.0): raise ValueError("Age")

        # 18. Education
        # EDUCA: 1-6.
        education = float(data['Education'])
        if not (1.0 <= education <= 6.0): raise ValueError("Education")

        # 19. Income
        # INCOME3: 1-11.
        income = float(data['Income'])
        if not (1.0 <= income <= 11.0): raise ValueError("Income")

        # Nếu tất cả đều qua, trả về dữ liệu đã được ép kiểu float
        validated_data = {
            "HighBP": high_bp, "HighChol": high_chol, "CholCheck": chol_check,
            "BMI": bmi, "Smoker": smoker, "Stroke": stroke,
            "HeartDiseaseorAttack": heart_disease, "PhysActivity": phys_activity,
            "HvyAlcoholConsump": hvy_alcohol, "AnyHealthcare": any_healthcare,
            "NoDocbcCost": no_doc_cost, "GenHlth": gen_hlth, "MentHlth": ment_hlth,
            "PhysHlth": phys_hlth, "DiffWalk": diff_walk, "Sex": sex,
            "Age": age, "Education": education, "Income": income
        }
        
        return True, validated_data

    except Exception as e:
        error_field = str(e)
        return False, f"Dữ liệu không hợp lệ hoặc thiếu cho trường: {error_field}. Vui lòng kiểm tra lại."