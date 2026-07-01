class AttentionEngine:

    def normalize_posture(self, angle):

        if angle is None:
            return 0.5

        angle = abs(angle)

        if angle >= 90:
            return 1.0

        if angle >= 80:
            return 0.9

        if angle >= 70:
            return 0.8

        if angle >= 60:
            return 0.6

        if angle >= 50:
            return 0.4

        return 0.2


    def normalize_csr(self, csr):

        if csr is None:
            return 0.5

        ideal = 1.7

        diff = abs(csr - ideal)

        score = max(
            0,
            1 - diff / 1.0
        )

        return score


    def normalize_swr(self, swr):

        if swr is None:
            return 0.5

        ideal = 2.3

        diff = abs(swr - ideal)

        score = max(
            0,
            1 - diff / 1.5
        )

        return score


    def calculate(
        self,
        gaze_score,
        posture,
        csr,
        swr
    ):

        posture_score = self.normalize_posture(posture)

        csr_score = self.normalize_csr(csr)

        swr_score = self.normalize_swr(swr)

        attention = (

            0.40 * gaze_score +

            0.30 * posture_score +

            0.15 * csr_score +

            0.15 * swr_score

        )

        return {

            "attention": round(attention,3),

            "gaze_score": round(gaze_score,3),

            "posture_score": round(posture_score,3),

            "csr_score": round(csr_score,3),

            "swr_score": round(swr_score,3)

        }


attention_engine = AttentionEngine()