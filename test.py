infile = open("student_info.txt", "r")
senior_avg = 0
senior_count = 0
score_list = []
for line in infile:
    word = line
    student_name = word.split()[0:1]
    hw1 = int(word.split()[2])
    hw5 = int(word.split()[6])
    status = word.split()[6].lower()

    if status == 'senior':
        senior_avg += hw1
        senior_count += 1
    else:
        score_list.append((hw5, student_name))

score_list.sort(reverse=True)
print('Student Name                       HW1')
print('-' * 20)
for score in score_list:
    print(score[1], " " * 20)
print('-' * 20)
print('HW1 Average Grade = ', senior_avg/senior_count)
print('HW5 Highest Grade = ', score_list[0][0])

