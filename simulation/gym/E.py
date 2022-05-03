class E:
    class A:
        CHOOSE_LOT_FOR_FREE_MACHINE = 100001
        CHOOSE_MACHINE_FOR_FREE_LOT = 100002
        CHOOSE_LOT_TO_DISPATCH = 100003

        class L4M:
            class S:
                class GLOBAL:
                    pass

                class MACHINE:
                    class MAINTENANCE:
                        NEXT = 4010101

                    SETUP_PROCESSING_RATIO = 4010010
                    IDLE_RATIO = 4010020
                    MACHINE_CLASS = 4010030

                class OPERATION_TYPE:
                    NO_LOTS = 4030010
                    NO_LOTS_PER_BATCH = 4030020

                    class STEPS_LEFT:
                        MIN = 4030101
                        MEAN = 4030102
                        MEDIAN = 4030103
                        MAX = 4030104

                    class FREE_SINCE:
                        MIN = 4030201
                        MEAN = 4030202
                        MEDIAN = 4030203
                        MAX = 4030204

                    class PRIORITY:
                        MIN = 4030401
                        MEAN = 4030402
                        MEDIAN = 4030403
                        MAX = 4030404

                    class PROCESSING_TIME:
                        AVERAGE = 4030501

                    class BATCH:
                        MIN = 4030601
                        MAX = 4030602
                        FULLNESS = 4030603

                    class CR:
                        MIN = 4030701
                        MEAN = 4030703
                        MEDIAN = 4030703
                        MAX = 4030704

                    class SETUP:
                        NEEDED = 4030801
                        MIN_RUNS_LEFT = 4030802
                        MIN_RUNS_OK = 4030803
                        LAST_SETUP_TIME = 4030804
